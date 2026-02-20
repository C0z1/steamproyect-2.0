"""
src/db/user_queries.py
=======================
Queries de DuckDB para usuarios, librería y wishlist.
"""
import logging
import math
from datetime import datetime
from typing import Optional
import duckdb

logger = logging.getLogger(__name__)

def _san(d: dict) -> dict:
    return {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
            for k, v in d.items()}


def upsert_user(con, steam_id: str, display_name: str, avatar_url: str, profile_url: str):
    con.execute("""
        INSERT INTO users (steam_id, display_name, avatar_url, profile_url, last_login)
        VALUES (?, ?, ?, ?, NOW())
        ON CONFLICT (steam_id) DO UPDATE SET
            display_name = excluded.display_name,
            avatar_url   = excluded.avatar_url,
            profile_url  = excluded.profile_url,
            last_login   = NOW()
    """, [steam_id, display_name, avatar_url, profile_url])


def get_user(con, steam_id: str) -> Optional[dict]:
    row = con.execute("SELECT * FROM users WHERE steam_id = ?", [steam_id]).fetchdf()
    return _san(row.iloc[0].to_dict()) if not row.empty else None


def sync_user_library(con, steam_id: str, games: list[dict]) -> int:
    """Guarda/actualiza la librería del usuario. Retorna cantidad insertada."""
    if not games:
        return 0
    inserted = 0
    for g in games:
        try:
            last_played = None
            if g.get("last_played") and g["last_played"] > 0:
                last_played = datetime.fromtimestamp(g["last_played"])
            con.execute("""
                INSERT INTO user_games (steam_id, appid, game_title, playtime_mins, last_played)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (steam_id, appid) DO UPDATE SET
                    game_title    = excluded.game_title,
                    playtime_mins = excluded.playtime_mins,
                    last_played   = excluded.last_played,
                    synced_at     = NOW()
            """, [steam_id, g["appid"], g.get("title"), g.get("playtime_mins", 0), last_played])
            inserted += 1
        except Exception as e:
            logger.debug(f"Error sync game {g.get('appid')}: {e}")
    return inserted


def sync_user_wishlist(con, steam_id: str, items: list[dict]) -> int:
    if not items:
        return 0
    inserted = 0
    for item in items:
        try:
            con.execute("""
                INSERT INTO user_wishlist (steam_id, appid, game_title)
                VALUES (?, ?, ?)
                ON CONFLICT (steam_id, appid) DO NOTHING
            """, [steam_id, item["appid"], item.get("title")])
            inserted += 1
        except Exception as e:
            logger.debug(f"Error sync wishlist {item.get('appid')}: {e}")
    return inserted


def get_user_library(con, steam_id: str) -> list[dict]:
    """Librería con datos de precio de nuestra DB."""
    rows = con.execute("""
        SELECT
            ug.appid, ug.game_title, ug.playtime_mins, ug.last_played,
            g.id AS game_id,
            COALESCE(stats.min_price, 0)    AS min_price,
            COALESCE(stats.avg_price, 0)    AS avg_price,
            COALESCE(stats.max_discount, 0) AS max_discount,
            COALESCE(stats.total_records, 0) AS total_records,
            -- Valor estimado pagado (aproximación usando precio promedio histórico)
            COALESCE(stats.avg_price, 0)    AS estimated_value
        FROM user_games ug
        LEFT JOIN games g ON g.appid = ug.appid
        LEFT JOIN (
            SELECT
                game_id,
                MIN(price_usd) AS min_price,
                AVG(price_usd) AS avg_price,
                MAX(cut_pct)   AS max_discount,
                COUNT(*)       AS total_records
            FROM price_history
            GROUP BY game_id
        ) stats ON stats.game_id = g.id
        WHERE ug.steam_id = ?
        ORDER BY ug.playtime_mins DESC
    """, [steam_id]).fetchdf()
    return [_san(r) for r in rows.to_dict(orient="records")]


def get_user_wishlist_with_prices(con, steam_id: str) -> list[dict]:
    """Wishlist con precios actuales y señales de alerta."""
    rows = con.execute("""
        WITH latest_price AS (
            SELECT
                game_id,
                price_usd, regular_usd, cut_pct,
                ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        )
        SELECT
            uw.appid,
            uw.game_title,
            uw.added_at,
            g.id AS game_id,
            COALESCE(lp.price_usd, 0)    AS current_price,
            COALESCE(lp.cut_pct, 0)      AS discount_pct,
            COALESCE(stats.min_price, 0) AS all_time_low,
            COALESCE(stats.avg_price, 0) AS avg_price,
            pc.score,
            pc.signal
        FROM user_wishlist uw
        LEFT JOIN games g ON g.appid = uw.appid
        LEFT JOIN (SELECT * FROM latest_price WHERE rn = 1) lp ON lp.game_id = g.id
        LEFT JOIN (
            SELECT game_id, MIN(price_usd) AS min_price, AVG(price_usd) AS avg_price
            FROM price_history GROUP BY game_id
        ) stats ON stats.game_id = g.id
        LEFT JOIN predictions_cache pc ON pc.game_id = g.id
        WHERE uw.steam_id = ?
        ORDER BY pc.score DESC NULLS LAST, lp.cut_pct DESC NULLS LAST
    """, [steam_id]).fetchdf()
    return [_san(r) for r in rows.to_dict(orient="records")]


def get_user_owned_appids(con, steam_id: str) -> set[int]:
    """Set de appids que el usuario ya posee."""
    rows = con.execute(
        "SELECT appid FROM user_games WHERE steam_id = ?", [steam_id]
    ).fetchdf()
    return set(rows["appid"].tolist()) if not rows.empty else set()


def get_recommendations(con, steam_id: str, limit: int = 12) -> list[dict]:
    """
    Recomendaciones personalizadas:
    - Juegos con BUY signal que el usuario NO tiene
    - Ordenados por score ML descendente
    - Excluyendo juegos de su librería y wishlist
    """
    rows = con.execute("""
        WITH owned AS (
            SELECT appid FROM user_games WHERE steam_id = ?
            UNION
            SELECT appid FROM user_wishlist WHERE steam_id = ?
        ),
        latest_price AS (
            SELECT
                game_id, price_usd, cut_pct,
                ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        )
        SELECT
            g.id, g.title, g.appid,
            pc.score, pc.signal, pc.reason,
            COALESCE(lp.price_usd, 0) AS current_price,
            COALESCE(lp.cut_pct, 0)   AS discount_pct,
            COALESCE(stats.min_price, 0) AS min_price
        FROM predictions_cache pc
        JOIN games g ON g.id = pc.game_id
        LEFT JOIN (SELECT * FROM latest_price WHERE rn = 1) lp ON lp.game_id = g.id
        LEFT JOIN (
            SELECT game_id, MIN(price_usd) AS min_price
            FROM price_history GROUP BY game_id
        ) stats ON stats.game_id = g.id
        WHERE pc.signal = 'BUY'
          AND g.appid IS NOT NULL
          AND g.appid NOT IN (SELECT appid FROM owned)
        ORDER BY pc.score DESC
        LIMIT ?
    """, [steam_id, steam_id, limit]).fetchdf()
    return [_san(r) for r in rows.to_dict(orient="records")]


def get_library_stats(con, steam_id: str) -> dict:
    """Stats de la librería del usuario."""
    row = con.execute("""
        SELECT
            COUNT(*)                      AS total_games,
            SUM(ug.playtime_mins) / 60.0  AS total_hours,
            COUNT(g.id)                   AS tracked_games
        FROM user_games ug
        LEFT JOIN games g ON g.appid = ug.appid
        WHERE ug.steam_id = ?
    """, [steam_id]).fetchone()
    return {
        "total_games":   int(row[0] or 0),
        "total_hours":   round(float(row[1] or 0), 1),
        "tracked_games": int(row[2] or 0),
    }
