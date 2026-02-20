"""
src/services/price_service.py
"""
import logging
import math
from datetime import datetime
from typing import Optional

from src.db import queries
from src.db.connection import get_db

logger = logging.getLogger(__name__)


def _sanitize(value):
    """Convierte NaN/Inf a None para que JSON no explote."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _clean_dict(d: dict) -> dict:
    """Aplica _sanitize a todos los valores de un dict."""
    return {k: _sanitize(v) for k, v in d.items()}


def get_game_history(
    game_id: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> dict:
    con = get_db()
    game = queries.get_game(con, game_id)
    if not game:
        raise ValueError(f"Juego no encontrado: {game_id}")

    history = queries.get_price_history(con, game_id, since=since, until=until)
    if not history:
        raise ValueError(f"Sin historial de precios para: {game_id}")

    cleaned = []
    for record in history:
        r = _clean_dict(record)
        if isinstance(r.get("timestamp"), datetime):
            r["timestamp"] = r["timestamp"].isoformat()
        cleaned.append(r)

    return {
        "game_id": game_id,
        "title": game.get("title"),
        "appid": game.get("appid"),
        "count": len(cleaned),
        "history": cleaned,
    }


def get_game_stats(game_id: str) -> dict:
    con = get_db()
    game = queries.get_game(con, game_id)
    if not game:
        raise ValueError(f"Juego no encontrado: {game_id}")

    stats = queries.get_price_stats(con, game_id)
    if not stats:
        raise ValueError(f"Sin stats para: {game_id}")

    seasonal = queries.get_seasonal_patterns(con, game_id)

    return {
        "game_id": game_id,
        "title": game.get("title"),
        "appid": game.get("appid"),
        "stats": _clean_dict(stats),
        "seasonal_patterns": [_clean_dict(s) for s in seasonal],
    }


def get_game_by_appid(appid: int) -> Optional[dict]:
    con = get_db()
    return queries.get_game_by_appid(con, appid)


def list_games(limit: int = 50, offset: int = 0) -> list[dict]:
    con = get_db()
    return [_clean_dict(g) for g in queries.list_games(con, limit=limit, offset=offset)]
