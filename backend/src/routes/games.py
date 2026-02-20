"""
src/routes/games.py
===================
Endpoints relacionados a juegos.
Solo validan input y delegan a los services.
"""

from fastapi import APIRouter, HTTPException, Query

from src.api.client import get_client
from src.services import price_service

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/search")
async def search_games(q: str = Query(..., min_length=1, description="Nombre del juego")):
    """Busca juegos por nombre en IsThereAnyDeal."""
    client = get_client()
    async with client:
        results = await client.search_games(q, limit=20)
    return [r.model_dump() for r in results]


@router.get("")
def list_games(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Lista juegos sincronizados con sus estadísticas básicas."""
    return price_service.list_games(limit=limit, offset=offset)


@router.get("/{game_id}")
def get_game(game_id: str):
    """Info básica de un juego + precio actual."""
    try:
        return price_service.get_game_stats(game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
