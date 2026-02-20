"""
src/services/sync_service.py
=============================
Sincronización de datos desde IsThereAnyDeal API → DuckDB.
Orquesta: SteamSpy → ITAD lookup → ITAD history → DuckDB upsert.
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
    """Obtiene los top appids de Steam via SteamSpy."""
    try:
        r = await client.get(
            "https://steamspy.com/api.php",
            params={"request": "top100forever"},
            timeout=30,
        )
        if r.status_code == 200:
            appids = [int(k) for k in r.json().keys()][:top_n]
            logger.info(f"SteamSpy: {len(appids)} appids obtenidos")
            return appids
    except Exception as e:
        logger.error(f"Error en SteamSpy: {e}")
    return []


async def sync_game(
    itad_client: ITADClient,
    appid: int,
    game_id: Optional[str] = None,
) -> dict:
    """
    Sincroniza un juego completo:
    1. Si no hay game_id, hace lookup en ITAD por appid
    2. Obtiene historial de precios
    3. Hace upsert en DuckDB

    Retorna: {"game_id": str, "inserted": int, "status": str}
    """
    con = get_db()

    async with ITADClient(settings.itad_api_key) as client:
        # 1. Si no hay game_id, hace lookup en ITAD por appid
        if not game_id:
            lookup = await client.lookup_game(appid)
            if not lookup:
                return {"appid": appid, "status": "not_found", "inserted": 0}
            game_id, slug, title = lookup
        else:
            slug, title = game_id, f"App {appid}"

        # 2. Guardar/actualizar el juego en la tabla games
        try:
            queries.upsert_game(con, game_id=game_id, slug=slug, title=title, appid=appid)
        except Exception as e:
            logger.debug(f"upsert_game skip (ya existe): {e}")

        # 3. Obtener historial de precios
        records = await client.get_price_history(game_id, appid=appid)
        if not records:
            return {"game_id": game_id, "appid": appid, "status": "no_history", "inserted": 0}

        # 4. Upsert en price_history
        rows = [r.model_dump() for r in records]
        inserted = queries.upsert_price_records(con, rows)

        logger.info(f"Sincronizado appid={appid} → {inserted} registros nuevos")
        return {"game_id": game_id, "appid": appid, "status": "ok", "inserted": inserted}


async def sync_top_games(top_n: int = 100) -> dict:
    """
    Sincroniza los top N juegos de Steam.
    Usado para la carga inicial de datos.

    Retorna resumen: {"total_games": int, "total_inserted": int, "errors": int}
    """
    if not settings.itad_api_key:
        raise ValueError("ITAD_API_KEY no configurada")

    summary = {"total_games": 0, "total_inserted": 0, "errors": 0, "synced": []}

    async with httpx.AsyncClient(timeout=30) as http_client:
        appids = await get_top_appids(http_client, top_n)

    if not appids:
        logger.error("No se obtuvieron appids de SteamSpy")
        return summary

    logger.info(f"Iniciando sync de {len(appids)} juegos...")

    async with ITADClient(settings.itad_api_key) as itad:
        batch_size = settings.request_batch_size

        for i in range(0, len(appids), batch_size):
            batch = appids[i:i + batch_size]

            # Lookup masivo en ITAD
            lookup_tasks = [itad.lookup_game(appid) for appid in batch]
            game_ids = await asyncio.gather(*lookup_tasks, return_exceptions=True)

            # Historial para los que encontramos
            for appid, lookup_result in zip(batch, game_ids):
                if isinstance(lookup_result, Exception) or not lookup_result:
                    summary["errors"] += 1
                    continue

                game_id, slug, title = lookup_result

                try:
                    con = get_db()

                    # Guardar juego con título real de ITAD
                    try:
                        queries.upsert_game(con, game_id=game_id, slug=slug,
                                            title=title, appid=appid)
                    except Exception as e:
                        logger.debug(f"upsert_game skip appid={appid}: {e}")

                    records = await itad.get_price_history(game_id, appid=appid)
                    if records:
                        rows = [r.model_dump() for r in records]
                        inserted = queries.upsert_price_records(con, rows)
                        summary["total_inserted"] += inserted
                        summary["total_games"] += 1
                        summary["synced"].append(appid)
                        logger.info(f"  ✓ {title} ({appid}): {inserted} registros")
                    else:
                        logger.debug(f"Sin historial para appid={appid} ({title})")
                        summary["errors"] += 1

                except Exception as e:
                    logger.warning(f"Error procesando appid={appid}: {e}")
                    summary["errors"] += 1

            # Rate limiting entre lotes
            await asyncio.sleep(settings.request_delay)
            logger.info(f"Progreso: {i + batch_size}/{len(appids)} | Insertados: {summary['total_inserted']}")

    logger.info(f"Sync completado: {summary}")
    return summary
