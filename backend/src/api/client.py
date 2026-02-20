"""
src/api/client.py
=================
Cliente HTTP para IsThereAnyDeal API.
Maneja: autenticación, retry con backoff, rate limiting, parsing de respuestas.

Una sola instancia se crea en el lifespan de FastAPI y se reutiliza.
"""

import asyncio
import logging
from typing import Optional

import httpx

from config import get_settings
from src.api.schemas import ITADLookupResponse, ITADGame, PriceRecord, ITADSearchResult

logger = logging.getLogger(__name__)

settings = get_settings()


class ITADClient:
    """
    Cliente async para IsThereAnyDeal API v2.
    Docs: https://itad.docs.apiary.io
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("ITAD_API_KEY es requerida")
        self._key = api_key
        self._base = settings.itad_base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.aclose()

    def _params(self, extra: dict) -> dict:
        """Agrega la API key a todos los requests."""
        return {"key": self._key, **extra}

    async def _get(self, path: str, params: dict, retries: int = 3) -> Optional[dict]:
        """GET con retry exponencial."""
        url = f"{self._base}{path}"
        for attempt in range(retries):
            try:
                r = await self._client.get(url, params=self._params(params))
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limit hit, esperando {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                logger.debug(f"HTTP {r.status_code} en {path}")
                return None
            except httpx.TimeoutException:
                logger.warning(f"Timeout en {path} (intento {attempt + 1})")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error en {path}: {e}")
                return None
        return None

    # ── Endpoints públicos ────────────────────────────────────────────────────

    async def lookup_game(self, appid: int) -> Optional[tuple[str, str, str]]:
        """
        Convierte un Steam appid en datos de ITAD.
        Retorna (game_id, slug, title) o None si no se encontró.
        """
        data = await self._get("/games/lookup/v1", {"appid": appid})
        if not data:
            return None
        try:
            resp = ITADLookupResponse(**data)
            if resp.found and resp.game:
                return (resp.game.id, resp.game.slug, resp.game.title)
            return None
        except Exception as e:
            logger.debug(f"Error parseando lookup para appid={appid}: {e}")
            return None

    async def get_price_history(
        self,
        game_id: str,
        appid: Optional[int] = None,
        since: Optional[str] = None,
    ) -> list[PriceRecord]:
        """
        Obtiene historial completo de precios de un juego.
        Retorna lista de PriceRecord normalizados.
        """
        params = {
            "id": game_id,
            "country": settings.itad_country,
            "since": since or settings.itad_history_since,
        }
        data = await self._get("/games/history/v2", params)
        if not data:
            logger.warning(f"history/v2 retornó vacío para game_id={game_id}")
            return []

        # Log estructura real para debug
        if isinstance(data, list):
            logger.info(f"history/v2 → lista de {len(data)} entradas. "
                        f"Primera: {str(data[0])[:200] if data else '(vacía)'}")
        else:
            logger.info(f"history/v2 → dict con keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

        records = []
        # La API devuelve una lista directa de price events
        entries = data if isinstance(data, list) else data.get("prices", [])

        for entry in entries:
            try:
                # Normalizar estructura (la API v2 puede variar)
                deal = entry.get("deal") or entry
                price_obj = deal.get("price") or entry.get("price") or {}
                regular_obj = deal.get("regular") or entry.get("regular") or {}
                shop = entry.get("shop") or {}

                records.append(PriceRecord(
                    game_id=game_id,
                    appid=appid,
                    timestamp=entry["timestamp"],
                    price_usd=float(price_obj.get("amount", 0)),
                    regular_usd=float(regular_obj.get("amount", 0)),
                    cut_pct=int(deal.get("cut", entry.get("cut", 0)) or 0),
                    shop_id=shop.get("id"),
                    shop_name=shop.get("name", "Steam"),
                ))
            except Exception as e:
                logger.debug(f"Error parseando entry de historial: {e}")
                continue

        return records

    async def search_games(self, query: str, limit: int = 20) -> list[ITADSearchResult]:
        """Busca juegos por nombre en ITAD."""
        data = await self._get("/games/search/v1", {"title": query, "results": limit})
        if not data:
            return []
        results = []
        for item in data if isinstance(data, list) else []:
            try:
                results.append(ITADSearchResult(**item))
            except Exception:
                continue
        return results

    async def get_current_prices(self, game_ids: list[str]) -> dict:
        """Obtiene precios actuales de múltiples juegos (batch)."""
        if not game_ids:
            return {}
        params = {
            "id": ",".join(game_ids),
            "country": settings.itad_country,
        }
        data = await self._get("/games/prices/v3", params)
        return data or {}
    
    async def get_game_info(self, game_id: str) -> Optional[tuple[str, str, str]]:
        """
        Obtiene título y slug de un juego por su ITAD game_id.
        Usa /games/info/v2. Retorna (game_id, slug, title) o None.
        """
        data = await self._get("/games/info/v2", {"id": game_id})
        if not data:
            return None
        try:
            # La API retorna un objeto con 'title' y 'slug'
            if isinstance(data, list) and data:
                item = data[0]
            elif isinstance(data, dict):
                item = data
            else:
                return None
            title = item.get("title") or item.get("name") or game_id
            slug  = item.get("slug") or game_id
            return (game_id, slug, title)
        except Exception as e:
            logger.debug(f"Error en get_game_info({game_id}): {e}")
            return None


# ── Factory ───────────────────────────────────────────────────────────────────

_client_instance: Optional[ITADClient] = None


def get_client() -> ITADClient:
    """Retorna la instancia singleton del cliente."""
    global _client_instance
    if _client_instance is None:
        _client_instance = ITADClient(settings.itad_api_key)
    return _client_instance


