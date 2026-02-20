"""
src/routes/sync.py
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from src.services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/game/{appid}")
async def sync_game_by_appid(appid: int):
    """Sincroniza un juego por Steam appid."""
    result = await sync_service.sync_by_appid(appid)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"appid {appid} no encontrado en ITAD")
    return result


@router.post("/id/{game_id:path}")
async def sync_game_by_id(game_id: str):
    """
    Sincroniza un juego por ITAD game_id.
    Llamado automáticamente desde el frontend cuando el usuario
    hace click en un resultado de búsqueda.
    """
    result = await sync_service.sync_by_game_id(game_id)
    return result


@router.post("/top")
async def sync_top_games(
    background_tasks: BackgroundTasks,
    top_n: int = Query(100, ge=10, le=500),
):
    """Sincroniza los top N juegos en segundo plano."""
    background_tasks.add_task(sync_service.sync_top_games, top_n)
    return {"status": "started", "message": f"Sincronizando top {top_n} juegos en segundo plano."}
