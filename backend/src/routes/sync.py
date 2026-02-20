"""
src/routes/sync.py
==================
Endpoints de sincronización de datos desde ITAD.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from src.services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/game/{appid}")
async def sync_game(appid: int):
    """
    Sincroniza un juego específico por Steam appid.
    Hace lookup en ITAD y trae su historial de precios.
    """
    result = await sync_service.sync_game(None, appid=appid)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"appid {appid} no encontrado en ITAD")
    return result


@router.post("/top")
async def sync_top_games(
    background_tasks: BackgroundTasks,
    top_n: int = Query(100, ge=10, le=500, description="Cantidad de juegos a sincronizar"),
):
    """
    Sincroniza los top N juegos de Steam en segundo plano.
    Retorna inmediatamente; el proceso corre async.
    """
    background_tasks.add_task(sync_service.sync_top_games, top_n)
    return {
        "status": "started",
        "message": f"Sincronizando top {top_n} juegos en segundo plano.",
    }
