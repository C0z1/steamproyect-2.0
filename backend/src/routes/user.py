"""
src/routes/user.py
==================
Endpoints del usuario autenticado: librería, wishlist, recomendaciones.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from src.api.steam_auth import decode_jwt
from src.api.steam_client import get_steam_client, _get_key
from src.db.connection import get_db
from src.db import user_queries
from src.services import sync_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/me", tags=["user"])


def _get_steam_id(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt(auth[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]


def _check_steam_key():
    try:
        _get_key()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/library")
async def get_library(request: Request, sync: bool = False):
    steam_id = _get_steam_id(request)
    con = get_db()

    if sync:
        try:
            steam = get_steam_client()
            games = await steam.get_owned_games(steam_id)
            if games:
                n = user_queries.sync_user_library(con, steam_id, games)
                logger.info(f"Sync directo: {n} juegos para {steam_id}")
            else:
                logger.warning(f"get_owned_games retorno 0 juegos para {steam_id}")
        except Exception as e:
            logger.error(f"Error sync libreria: {e}")

    library = user_queries.get_user_library(con, steam_id)
    stats   = user_queries.get_library_stats(con, steam_id)
    return {"steam_id": steam_id, "stats": stats, "games": library}


@router.post("/library/sync")
async def sync_library(request: Request, background_tasks: BackgroundTasks):
    steam_id = _get_steam_id(request)
    _check_steam_key()

    async def do_sync():
        try:
            con = get_db()
            steam = get_steam_client()
            games = await steam.get_owned_games(steam_id)
            if games:
                n = user_queries.sync_user_library(con, steam_id, games)
                logger.info(f"Background sync OK: {n} juegos para {steam_id}")
            else:
                logger.warning(f"Background sync: 0 juegos — perfil privado o key invalida")
        except Exception as e:
            logger.error(f"Background sync fallo: {e}")

    background_tasks.add_task(do_sync)
    return {"status": "syncing", "message": "Library sync started"}


@router.get("/wishlist")
async def get_wishlist(request: Request, sync: bool = False):
    steam_id = _get_steam_id(request)
    con = get_db()

    if sync:
        try:
            steam = get_steam_client()
            items = await steam.get_wishlist(steam_id)
            if items:
                user_queries.sync_user_wishlist(con, steam_id, items)
                for item in items[:10]:
                    if item.get("appid"):
                        try:
                            await sync_service.sync_by_appid(item["appid"])
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Error sync wishlist: {e}")

    wishlist = user_queries.get_user_wishlist_with_prices(con, steam_id)
    return {"steam_id": steam_id, "wishlist": wishlist}


@router.get("/recommendations")
def get_recommendations(request: Request, limit: int = 12):
    steam_id = _get_steam_id(request)
    con = get_db()
    recs = user_queries.get_recommendations(con, steam_id, limit=limit)
    return {"steam_id": steam_id, "recommendations": recs}


@router.get("/owned/{appid}")
def check_owned(request: Request, appid: int):
    steam_id = _get_steam_id(request)
    con = get_db()
    owned = appid in user_queries.get_user_owned_appids(con, steam_id)
    return {"appid": appid, "owned": owned}
