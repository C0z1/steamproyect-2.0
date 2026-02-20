"""
src/services/price_service.py
==============================
Lógica de negocio para datos de precios.
Punto de entrada para los routes — nunca acceden a DB directamente.
"""

import logging
from datetime import datetime
from typing import Optional

from src.db import queries
from src.db.connection import get_db

logger = logging.getLogger(__name__)


def get_game_history(
    game_id: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> dict:
    """
    Retorna el historial de precios de un juego con metadata.
    Lanza ValueError si no existe el juego o no hay historial.
    """
    con = get_db()

    game = queries.get_game(con, game_id)
    if not game:
        raise ValueError(f"Juego no encontrado: {game_id}")

    history = queries.get_price_history(con, game_id, since=since, until=until)
    if not history:
        raise ValueError(f"Sin historial de precios para: {game_id}")

    # Serializar timestamps
    for record in history:
        if isinstance(record.get("timestamp"), datetime):
            record["timestamp"] = record["timestamp"].isoformat()

    return {
        "game_id": game_id,
        "title": game.get("title"),
        "appid": game.get("appid"),
        "count": len(history),
        "history": history,
    }


def get_game_stats(game_id: str) -> dict:
    """
    Retorna estadísticas agregadas de precio para un juego.
    Incluye patrones estacionales.
    """
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
        "stats": stats,
        "seasonal_patterns": seasonal,
    }


def get_game_by_appid(appid: int) -> Optional[dict]:
    """Busca un juego por su Steam appid."""
    con = get_db()
    return queries.get_game_by_appid(con, appid)


def list_games(limit: int = 50, offset: int = 0) -> list[dict]:
    """Lista de juegos con sus estadísticas básicas."""
    con = get_db()
    return queries.list_games(con, limit=limit, offset=offset)
