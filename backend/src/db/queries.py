"""
src/db/queries.py
=================
Todas las queries reutilizables contra DuckDB.
Ningún otro módulo escribe SQL — solo llaman funciones de aquí.
"""

import logging
from datetime import datetime
from typing import Optional

import duckdb

logger = logging.getLogger(__name__)


# ── games ─────────────────────────────────────────────────────────────────────

def upsert_game(con: duckdb.DuckDBPyConnection, game_id: str, slug: str, title: str, appid: Optional[int] = None):
    """
    Inserta o actualiza un juego.
    DuckDB no permite DO UPDATE SET en columnas referenciadas por un índice UNIQUE,
    así que usamos INSERT OR IGNORE + UPDATE separado.
    """
    # Intenta insertar; si ya existe el id, no hace nada
    con.execute("""
        INSERT INTO games (id, slug, title, appid)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (id) DO NOTHING
    """, [game_id, slug, title, appid])

    # Actualiza slug y title (nunca toca appid para no violar el índice unique)
    con.execute("""
        UPDATE games
        SET slug = ?, title = ?
        WHERE id = ?
    """, [slug, title, game_id])


def get_game(con: duckdb.DuckDBPyConnection, game_id: str) -> Optional[dict]:
    row = con.execute("SELECT * FROM games WHERE id = ?", [game_id]).fetchdf()
    return row.iloc[0].to_dict() if not row.empty else None


def get_game_by_appid(con: duckdb.DuckDBPyConnection, appid: int) -> Optional[dict]:
    row = con.execute("SELECT * FROM games WHERE appid = ?", [appid]).fetchdf()
    return row.iloc[0].to_dict() if not row.empty else None


def list_games(con: duckdb.DuckDBPyConnection, limit: int = 50, offset: int = 0) -> list[dict]:
    import math
    rows = con.execute("""
        SELECT g.id, g.title, g.appid, g.slug,
               COUNT(ph.id)                    AS total_records,
               COALESCE(MIN(ph.price_usd), 0)  AS min_price,
               COALESCE(MAX(ph.cut_pct), 0)    AS max_discount
        FROM games g
        LEFT JOIN price_history ph ON g.id = ph.game_id
        GROUP BY g.id, g.title, g.appid, g.slug
        ORDER BY total_records DESC
        LIMIT ? OFFSET ?
    """, [limit, offset]).fetchdf()
    result = []
    for r in rows.to_dict(orient="records"):
        result.append({k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                       for k, v in r.items()})
    return result


# ── price_history ─────────────────────────────────────────────────────────────

def upsert_price_records(con: duckdb.DuckDBPyConnection, records: list[dict]) -> int:
    """
    Inserta registros de precio evitando duplicados.
    Retorna la cantidad de filas insertadas.

    Notas DuckDB:
    - El id es autoincremental via SEQUENCE, NO se pasa en el INSERT.
    - Se cuenta antes/después porque ON CONFLICT DO NOTHING no retorna nada útil en DuckDB.
    - Contamos filas ANTES y DESPUÉS para saber cuántas se insertaron realmente.
    """
    if not records:
        return 0

    import pandas as pd

    # Aseguramos que el df NO tenga columna 'id' (viene de model_dump de PriceRecord)
    df = pd.DataFrame(records)
    df = df.drop(columns=['id'], errors='ignore')

    # Columnas que existen en price_history (sin 'id' — lo maneja la SEQUENCE)
    cols = ['game_id', 'appid', 'timestamp', 'price_usd', 'regular_usd', 'cut_pct', 'shop_id', 'shop_name']
    df = df[[c for c in cols if c in df.columns]]

    before = con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]

    con.register("_price_batch", df)
    con.execute(f"""
        INSERT INTO price_history ({', '.join(df.columns)})
        SELECT {', '.join(df.columns)}
        FROM _price_batch
        ON CONFLICT (game_id, timestamp, shop_id) DO NOTHING
    """)
    con.unregister("_price_batch")

    after = con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    inserted = after - before
    logger.debug(f"Insertados {inserted} registros de precio (de {len(records)} intentados)")
    return inserted


def get_price_history(
    con: duckdb.DuckDBPyConnection,
    game_id: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    shop_id: Optional[int] = None,
) -> list[dict]:
    """Historial de precios con filtros opcionales."""
    filters = ["game_id = ?"]
    params = [game_id]

    if since:
        filters.append("timestamp >= ?")
        params.append(since)
    if until:
        filters.append("timestamp <= ?")
        params.append(until)
    if shop_id:
        filters.append("shop_id = ?")
        params.append(shop_id)

    where = " AND ".join(filters)
    rows = con.execute(f"""
        SELECT timestamp, price_usd, regular_usd, cut_pct, shop_name
        FROM price_history
        WHERE {where}
        ORDER BY timestamp ASC
    """, params).fetchdf()
    return rows.to_dict(orient="records")


def get_price_stats(con: duckdb.DuckDBPyConnection, game_id: str) -> Optional[dict]:
    """Estadísticas agregadas de precio para un juego."""
    import math
    row = con.execute("""
        SELECT
            COUNT(*)                                AS total_records,
            MIN(timestamp)::VARCHAR                 AS first_seen,
            MAX(timestamp)::VARCHAR                 AS last_seen,
            COALESCE(MIN(price_usd), 0)             AS min_price,
            COALESCE(MAX(price_usd), 0)             AS max_price,
            COALESCE(ROUND(AVG(price_usd), 2), 0)   AS avg_price,
            COALESCE(MAX(cut_pct), 0)               AS max_discount,
            COALESCE(ROUND(AVG(cut_pct)
                FILTER (WHERE cut_pct > 0), 1), 0)  AS avg_discount_when_on_sale,
            COALESCE(ROUND(AVG(cut_pct)
                FILTER (WHERE MONTH(timestamp) IN (11,12)), 1), 0) AS avg_cut_q4,
            COALESCE(ROUND(AVG(cut_pct)
                FILTER (WHERE MONTH(timestamp) IN (6,7)), 1), 0)   AS avg_cut_summer,
            COALESCE(DATEDIFF('day', MIN(timestamp) FILTER (
                WHERE price_usd = (SELECT MIN(price_usd) FROM price_history WHERE game_id = ph.game_id)
            ), NOW()), 0)                            AS days_since_min_price
        FROM price_history ph
        WHERE game_id = ?
    """, [game_id]).fetchdf()
    if row.empty:
        return None
    # Sanitize any remaining NaN/Inf that pandas may produce for NULL integers
    return {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
            for k, v in row.iloc[0].to_dict().items()}


def get_seasonal_patterns(con: duckdb.DuckDBPyConnection, game_id: str) -> list[dict]:
    """Descuento promedio por mes para detectar patrones estacionales."""
    rows = con.execute("""
        SELECT
            MONTH(timestamp)                AS month,
            ROUND(AVG(cut_pct), 1)          AS avg_discount,
            COUNT(*)                        AS sample_count
        FROM price_history
        WHERE game_id = ? AND cut_pct > 0
        GROUP BY MONTH(timestamp)
        ORDER BY month
    """, [game_id]).fetchdf()
    return rows.to_dict(orient="records")


# ── predictions_cache ─────────────────────────────────────────────────────────

def get_cached_prediction(con: duckdb.DuckDBPyConnection, game_id: str, max_age_hours: int = 6) -> Optional[dict]:
    """Retorna predicción cacheada si existe y no expiró."""
    row = con.execute("""
        SELECT score, signal, reason, features, computed_at
        FROM predictions_cache
        WHERE game_id = ?
          AND computed_at > NOW() - INTERVAL (? || ' hours')
    """, [game_id, str(max_age_hours)]).fetchdf()
    return row.iloc[0].to_dict() if not row.empty else None


def upsert_prediction(con: duckdb.DuckDBPyConnection, game_id: str, score: float,
                      signal: str, reason: str, features: dict):
    """Guarda o actualiza la predicción cacheada."""
    import json
    con.execute("""
        INSERT INTO predictions_cache (game_id, score, signal, reason, features, computed_at)
        VALUES (?, ?, ?, ?, ?, NOW())
        ON CONFLICT (game_id) DO UPDATE SET
            score       = excluded.score,
            signal      = excluded.signal,
            reason      = excluded.reason,
            features    = excluded.features,
            computed_at = NOW()
    """, [game_id, score, signal, reason, json.dumps(features)])


# ── Overview / Dashboard ───────────────────────────────────────────────────────

def get_overview_stats(con: duckdb.DuckDBPyConnection) -> dict:
    """Stats globales para el dashboard."""
    import math
    row = con.execute("""
        SELECT
            (SELECT COUNT(*) FROM games)                        AS total_games,
            (SELECT COUNT(*) FROM price_history)                AS total_records,
            (SELECT COUNT(DISTINCT game_id) FROM predictions_cache
             WHERE signal = 'BUY')                             AS buy_signals,
            (SELECT COUNT(DISTINCT game_id) FROM predictions_cache
             WHERE signal = 'WAIT')                            AS wait_signals
    """).fetchone()
    return {
        "total_games":   row[0] or 0,
        "total_records": row[1] or 0,
        "buy_signals":   row[2] or 0,
        "wait_signals":  row[3] or 0,
    }


def get_top_deals(con: duckdb.DuckDBPyConnection, limit: int = 12) -> list[dict]:
    """
    Juegos con los mejores descuentos actuales (último registro de precio).
    DuckDB no tiene DISTINCT ON — usamos ROW_NUMBER() OVER.
    """
    import math
    rows = con.execute("""
        WITH ranked AS (
            SELECT
                game_id, price_usd, regular_usd, cut_pct, timestamp,
                ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        ),
        latest AS (
            SELECT game_id, price_usd, regular_usd, cut_pct, timestamp
            FROM ranked WHERE rn = 1
        ),
        mins AS (
            SELECT game_id, MIN(price_usd) AS min_price
            FROM price_history GROUP BY game_id
        )
        SELECT
            g.id, g.title, g.appid, g.slug,
            l.price_usd   AS current_price,
            l.regular_usd AS regular_price,
            l.cut_pct     AS discount_pct,
            l.timestamp::VARCHAR AS last_seen,
            COALESCE(m.min_price, l.price_usd) AS min_price
        FROM latest l
        JOIN games g ON g.id = l.game_id
        JOIN mins m ON m.game_id = l.game_id
        WHERE l.cut_pct > 0
        ORDER BY l.cut_pct DESC, l.price_usd ASC
        LIMIT ?
    """, [limit]).fetchdf()

    result = []
    for r in rows.to_dict(orient="records"):
        result.append({k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                       for k, v in r.items()})
    return result


def get_best_predictions(con: duckdb.DuckDBPyConnection, signal: str = "BUY", limit: int = 12) -> list[dict]:
    """Juegos con mejor score de predicción."""
    import math
    rows = con.execute("""
        WITH ranked_price AS (
            SELECT
                game_id, price_usd, cut_pct,
                ROW_NUMBER() OVER (PARTITION BY game_id ORDER BY timestamp DESC) AS rn
            FROM price_history
        ),
        latest_price AS (
            SELECT game_id, price_usd, cut_pct FROM ranked_price WHERE rn = 1
        )
        SELECT
            g.id, g.title, g.appid,
            pc.score, pc.signal, pc.reason,
            COALESCE(lp.price_usd, 0)  AS current_price,
            COALESCE(lp.cut_pct, 0)    AS discount_pct
        FROM predictions_cache pc
        JOIN games g ON g.id = pc.game_id
        LEFT JOIN latest_price lp ON lp.game_id = pc.game_id
        WHERE pc.signal = ?
        ORDER BY pc.score DESC
        LIMIT ?
    """, [signal, limit]).fetchdf()

    result = []
    for r in rows.to_dict(orient="records"):
        result.append({k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                       for k, v in r.items()})
    return result
