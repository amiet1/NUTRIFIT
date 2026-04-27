import logging
import os
from typing import Optional
from urllib.parse import urlencode

import httpx
from core.auth import (
    IDTokenValidationError,
    build_authorization_url,
    build_logout_url,
    generate_code_challenge,
    generate_code_verifier,
    generate_nonce,
    generate_state,
    validate_id_token,
)
from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from models.auth import User
from schemas.auth import (
    PlatformTokenExchangeRequest,
    TokenExchangeResponse,
    UserResponse,
)
from services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


def _local_patch(url: str) -> str:
    """Patch URL for local development."""
    if os.getenv("LOCAL_PATCH", "").lower() not in ("true", "1"):
        return url

    patched_url = url.replace("https://", "http://").replace(":8000", ":3000")
    logger.debug("[get_dynamic_backend_url] patching URL from %s to %s", url, patched_url)
    return patched_url


def get_dynamic_backend_url(request: Request) -> str:
    """Get backend URL dynamically from request headers."""
    mgx_external_domain = request.headers.get("mgx-external-domain")
    x_forwarded_host = request.headers.get("x-forwarded-host")
    host = request.headers.get("host")
    scheme = request.headers.get("x-forwarded-proto", "https")

    effective_host = mgx_external_domain or x_forwarded_host or host
    if not effective_host:
        return settings.backend_url

    return _local_patch(f"{scheme}://{effective_host}")


def derive_name_from_email(email: str) -> str:
    return email.split("@", 1)[0] if email else ""


@router.get("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """Start OIDC login flow with PKCE."""
    state, nonce, code_verifier = generate_state(), generate_nonce(), generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    auth_service = AuthService(db)
    await auth_service.store_oidc_state(state, nonce, code_verifier)

    backend_url = get_dynamic_backend_url(request)
    redirect_uri = f"{backend_url}/api/v1/auth/callback"
    
    auth_url = build_authorization_url(state, nonce, code_challenge, redirect_uri=redirect_uri)
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle OIDC callback."""
    backend_url = get_dynamic_backend_url(request)

    def redirect_with_error(message: str) -> RedirectResponse:
        fragment = urlencode({"msg": message})
        return RedirectResponse(url=f"{backend_url}/auth/error?{fragment}", status_code=status.HTTP_302_FOUND)

    if error: return redirect_with_error(f"OIDC error: {error}")
    if not code or not state: return redirect_with_error("Missing code or state")

    auth_service = AuthService(db)
    temp_data = await auth_service.get_and_delete_oidc_state(state)
    if not temp_data: return redirect_with_error("Invalid/expired state")

    nonce, code_verifier = temp_data["nonce"], temp_data.get("code_verifier")

    try:
        redirect_uri = f"{backend_url}/api/v1/auth/callback"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.oidc_client_id,
            "client_secret": settings.oidc_client_secret,
        }
        if code_verifier: token_data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            token_response = await client.post(f"{settings.oidc_issuer_url}/token", data=token_data)
        
        if token_response.status_code != 200: return redirect_with_error("Token exchange failed")

        tokens = token_response.json()
        id_claims = await validate_id_token(tokens.get("id_token"))
        if id_claims.get("nonce") != nonce: return redirect_with_error("Invalid nonce")

        user = await auth_service.get_or_create_user(
            platform_sub=id_claims["sub"], 
            email=id_claims.get("email", ""), 
            name=id_claims.get("name") or derive_name_from_email(id_claims.get("email"))
        )

        app_token, expires_at, _ = await auth_service.issue_app_token(user=user)
        fragment = urlencode({"token": app_token, "expires_at": int(expires_at.timestamp()), "token_type": "Bearer"})
        return RedirectResponse(url=f"{backend_url}/auth/callback?{fragment}", status_code=status.HTTP_302_FOUND)

    except Exception as e:
        logger.exception(f"OIDC callback error: {e}")
        return redirect_with_error("Authentication failed")


@router.post("/token/exchange", response_model=TokenExchangeResponse)
async def exchange_platform_token(
    payload: PlatformTokenExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Platform token for app token (Bypass for Local Dev)."""
    logger.info("[token/exchange] Manual bypass triggered for Admin")

    # Uses values from your .env
    admin_id = "marcy_admin_001"
    admin_email = getattr(settings, "admin_user_email", "admin@nutrifit.com")

    auth_service = AuthService(db)
    user = User(id=admin_id, email=admin_email, name="Marcy Admin", role="admin")

    app_token, expires_at, _ = await auth_service.issue_app_token(user=user)
    return TokenExchangeResponse(token=app_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info from JWT."""
    return current_user


@router.get("/logout")
async def logout():
    """Logout user."""
    return {"redirect_url": build_logout_url()}