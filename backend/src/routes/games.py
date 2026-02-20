"""src/routes/games.py"""
from fastapi import APIRouter, HTTPException, Query
from src.api.client import ITADClient
from src.services import price_service, sync_service
from src.db.connection import get_db
from src.db import queries
from config import get_settings

router = APIRouter(prefix="/games", tags=["games"])
settings = get_settings()


@router.get("/search")
async def search_games(q: str = Query(..., min_length=1)):
    async with ITADClient(settings.itad_api_key) as client:
        results = await client.search_games(q, limit=20)
    return [r.model_dump() for r in results]


@router.get("/top/deals")
def top_deals(limit: int = Query(12, ge=1, le=50)):
    """Top juegos con mejor descuento activo."""
    con = get_db()
    return queries.get_top_deals(con, limit=limit)


@router.get("/top/buy")
def top_buy_signals(limit: int = Query(12, ge=1, le=50)):
    """Top juegos con señal BUY del modelo."""
    con = get_db()
    return queries.get_best_predictions(con, signal="BUY", limit=limit)


@router.get("")
def list_games(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return price_service.list_games(limit=limit, offset=offset)


@router.get("/{game_id}/current-prices")
async def get_current_prices(game_id: str):
    """Precios actuales en todas las tiendas (via ITAD)."""
    async with ITADClient(settings.itad_api_key) as client:
        data = await client.get_current_prices([game_id])
    if not data:
        return {"game_id": game_id, "deals": []}
    # Normalizar respuesta de ITAD /games/prices/v3
    deals = []
    items = data if isinstance(data, list) else data.get("list", [data])
    for item in items:
        if not isinstance(item, dict):
            continue
        for deal in item.get("deals", []):
            shop = deal.get("shop") or {}
            price = deal.get("price") or {}
            regular = deal.get("regular") or {}
            deals.append({
                "shop_id":      shop.get("id"),
                "shop_name":    shop.get("name", "Unknown"),
                "price_usd":    price.get("amount", 0),
                "regular_usd":  regular.get("amount", 0),
                "cut_pct":      deal.get("cut", 0),
                "url":          deal.get("url"),
            })
    deals.sort(key=lambda x: x["price_usd"])
    return {"game_id": game_id, "deals": deals}


@router.get("/{game_id}")
def get_game(game_id: str):
    try:
        return price_service.get_game_stats(game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
