"""
src/routes/auth.py
==================
Endpoints de autenticación Steam OpenID.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from config import get_settings
from src.api.steam_auth import get_openid_redirect_url, verify_openid_response, create_jwt
from src.api.steam_client import get_steam_client
from src.db.connection import get_db
from src.db import user_queries

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = "http://localhost:3000"


@router.get("/steam")
def login_with_steam():
    """Inicia el flujo OpenID — redirige al usuario a Steam."""
    callback = f"http://localhost:8000/auth/steam/callback"
    redirect_url = get_openid_redirect_url(callback)
    return RedirectResponse(redirect_url)


@router.get("/steam/callback")
async def steam_callback(request: Request):
    """
    Steam redirige aquí tras autenticarse.
    Verificamos la identidad, obtenemos el perfil y emitimos un JWT.
    """
    params = dict(request.query_params)
    steam_id = await verify_openid_response(params)

    if not steam_id:
        raise HTTPException(status_code=401, detail="Steam authentication failed")

    # Obtener perfil de Steam
    steam = get_steam_client()
    profile = await steam.get_player_summary(steam_id)

    display_name = profile.get("personaname", f"User {steam_id}") if profile else f"User {steam_id}"
    avatar_url   = profile.get("avatarfull", "") if profile else ""
    profile_url  = profile.get("profileurl", "") if profile else ""

    # Guardar/actualizar usuario en DB
    con = get_db()
    user_queries.upsert_user(con, steam_id, display_name, avatar_url, profile_url)

    # Emitir JWT
    token = create_jwt(steam_id, display_name, avatar_url)

    # Redirigir al frontend con el token
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?token={token}")


@router.get("/me")
async def get_me(request: Request):
    """Retorna el usuario actual basado en el token JWT."""
    from src.api.steam_auth import decode_jwt
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token")
    token = auth[7:]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "steam_id":    payload["sub"],
        "display_name": payload["name"],
        "avatar_url":  payload.get("avatar", ""),
    }
