"""
src/services/sync_service.py
"""
import asyncio
import logging
from typing import Optional
import httpx
from config import get_settings
from src.api.client import ITADClient
from src.db import queries
from src.db.connection import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_top_appids(client: httpx.AsyncClient, top_n: int) -> list[int]:
    try:
        r = await client.get("https://steamspy.com/api.php",
                             params={"request": "top100forever"}, timeout=30)
        if r.status_code == 200:
            appids = [int(k) for k in r.json().keys()][:top_n]
            logger.info(f"SteamSpy: {len(appids)} appids obtenidos")
            return appids
    except Exception as e:
        logger.error(f"Error en SteamSpy: {e}")
    return []


async def sync_by_appid(appid: int) -> dict:
    """Sincroniza un juego por Steam appid. Usado por POST /sync/game/{appid}."""
    con = get_db()
    async with ITADClient(settings.itad_api_key) as client:
        lookup = await client.lookup_game(appid)
        if not lookup:
            return {"appid": appid, "status": "not_found", "inserted": 0}
        game_id, slug, title = lookup
        try:
            queries.upsert_game(con, game_id=game_id, slug=slug, title=title, appid=appid)
        except Exception as e:
            logger.debug(f"upsert_game skip appid={appid}: {e}")
        records = await client.get_price_history(game_id, appid=appid)
        if not records:
            return {"game_id": game_id, "title": title, "appid": appid,
                    "status": "no_history", "inserted": 0}
        inserted = queries.upsert_price_records(con, [r.model_dump() for r in records])
        logger.info(f"✓ {title} ({appid}): {inserted} registros")
        return {"game_id": game_id, "title": title, "appid": appid,
                "status": "ok", "inserted": inserted}


async def sync_by_game_id(game_id: str) -> dict:
    """
    Sincroniza un juego por ITAD game_id.
    Usado cuando el usuario hace click en un resultado de búsqueda —
    ya tenemos el game_id de ITAD pero el juego puede no estar en DB.
    """
    con = get_db()
    existing = queries.get_game(con, game_id)
    if not existing:
        try:
            queries.upsert_game(con, game_id=game_id, slug=game_id,
                                title=game_id, appid=None)
        except Exception:
            pass
    async with ITADClient(settings.itad_api_key) as client:
        records = await client.get_price_history(game_id)
        if not records:
            return {"game_id": game_id, "status": "no_history", "inserted": 0}
        inserted = queries.upsert_price_records(con, [r.model_dump() for r in records])
        logger.info(f"✓ game_id={game_id}: {inserted} registros")
        return {"game_id": game_id, "status": "ok", "inserted": inserted}


async def sync_top_games(top_n: int = 100) -> dict:
    if not settings.itad_api_key:
        raise ValueError("ITAD_API_KEY no configurada")
    summary = {"total_games": 0, "total_inserted": 0, "errors": 0, "synced": []}
    async with httpx.AsyncClient(timeout=30) as http_client:
        appids = await get_top_appids(http_client, top_n)
    if not appids:
        return summary
    logger.info(f"Iniciando sync de {len(appids)} juegos...")
    con = get_db()
    async with ITADClient(settings.itad_api_key) as itad:
        batch_size = settings.request_batch_size
        for i in range(0, len(appids), batch_size):
            batch = appids[i:i + batch_size]
            lookup_results = await asyncio.gather(
                *[itad.lookup_game(appid) for appid in batch],
                return_exceptions=True
            )
            for appid, lookup in zip(batch, lookup_results):
                if isinstance(lookup, Exception) or not lookup:
                    summary["errors"] += 1
                    continue
                game_id, slug, title = lookup
                try:
                    try:
                        queries.upsert_game(con, game_id=game_id, slug=slug,
                                            title=title, appid=appid)
                    except Exception as e:
                        logger.debug(f"upsert_game skip {appid}: {e}")
                    records = await itad.get_price_history(game_id, appid=appid)
                    if records:
                        inserted = queries.upsert_price_records(
                            con, [r.model_dump() for r in records])
                        summary["total_inserted"] += inserted
                        summary["total_games"] += 1
                        summary["synced"].append(appid)
                        logger.info(f"  ✓ {title} ({appid}): {inserted} registros")
                    else:
                        summary["errors"] += 1
                except Exception as e:
                    logger.warning(f"Error appid={appid}: {e}")
                    summary["errors"] += 1
            await asyncio.sleep(settings.request_delay)
            logger.info(f"Progreso: {min(i+batch_size,len(appids))}/{len(appids)} | "
                        f"Insertados: {summary['total_inserted']}")
    logger.info(f"Sync completado: {summary}")
    return summary
