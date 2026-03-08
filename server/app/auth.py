import uuid
import time
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from starlette.requests import Request

from app.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES, FRONTEND_URL
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── One-time OAuth tokens (replaces global token_store) ──────────────────────
auth_tokens: dict = {}


# ── Google OAuth Flow ─────────────────────────────────────────────────────────
def get_google_flow() -> Flow:
    """Used for user authentication only — not for calendar."""
    client_config = {
        "web": {
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/google")
async def auth_google(request: Request):
    flow = get_google_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    request.session["oauth_state"] = state
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_callback(request: Request, code: str):
    try:
        flow = get_google_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        user_info_service = build("oauth2", "v2", credentials=creds)
        user_info = user_info_service.userinfo().get().execute()

        # ✅ Generate one-time token — avoids cross-origin cookie issue
        token = str(uuid.uuid4())
        auth_tokens[token] = {
            "user": {
                "email":     user_info.get("email"),
                "name":      user_info.get("name"),
                "picture":   user_info.get("picture"),
                "logged_in": True,
            },
            "expires_at": time.time() + 60   # expires in 60 seconds
        }

        logger.info(f"OAuth success for: {user_info.get('email')}")
        return RedirectResponse(url=f"{FRONTEND_URL}?auth_token={token}")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
async def verify_token(request: Request, token: str):
    """Frontend calls this to exchange one-time token for a session."""
    entry = auth_tokens.pop(token, None)   # ✅ one-time use — deleted immediately

    if not entry:
        raise HTTPException(status_code=401, detail="Invalid token")

    if time.time() > entry["expires_at"]:
        raise HTTPException(status_code=401, detail="Token expired")

    request.session["user"] = entry["user"]
    logger.info(f"Session created for: {entry['user']['email']}")
    return {"authenticated": True, "user": entry["user"]}


@router.get("/status")
async def auth_status(request: Request):
    user = request.session.get("user")
    if user and user.get("logged_in"):
        return {"authenticated": True, "user": user}
    return {"authenticated": False}


@router.post("/logout")
async def logout(request: Request):
    user = request.session.get("user")
    if user:
        logger.info(f"Logout: {user.get('email')}")
    request.session.clear()
    return {"success": True, "message": "Logged out successfully"}


@router.get("/my-token")
async def get_my_token(request: Request):
    """One-time use — get refresh token to store in .env"""
    user = request.session.get("user")
    if not user:
        return {"error": "Not authenticated. Login first."}
    return user