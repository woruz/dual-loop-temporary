from fastapi import Response
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.server.dependencies import (
    get_auth_repo,
    get_github_oauth,
    get_password_hasher,
    get_token_generator,
    get_current_user
)
from app.core.use_cases.register_user import RegisterUser
from app.core.use_cases.login_user import LoginUser
from app.core.use_cases.github_oauth_login import GitHubOAuthLogin

logger =logging.getLogger("app.server.routers.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

class EmailPasswordBody(BaseModel):
    email: EmailStr
    password: str

# ── Email / Password ──────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: EmailPasswordBody,
    response: Response, # Inject FastAPI Response object
    repo=Depends(get_auth_repo),
    hasher=Depends(get_password_hasher),
    token_generator=Depends(get_token_generator),
):
    logger.info(f"API Request: POST /auth/register: email='{body.email}' registeration requested")
    try:

        user = await RegisterUser(repo, hasher).execute(body.email, body.password)
        access_token = token_generator.generate_token(user.id, user.email)
        
        # Set the HttpOnly Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,        # JavaScript cannot access it
            secure=True,          # Only sent over HTTPS
            samesite="lax",       # Protects against CSRF
            max_age=1440 * 60,    # 24 hours in seconds
            path="/",
        )
        
        logger.info(f"API Success: POST /auth/register: email='{user.email}' registered")
        return {"id": str(user.id), "email": user.email}
    except ValueError as e:
        logger.warning(f"API Failure: POST /auth/register error: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.error(f"API Error: POST /auth/register unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")


@router.post("/login")
async def login(
    body: EmailPasswordBody,
    response: Response, # Inject FastAPI Response object
    repo=Depends(get_auth_repo),
    hasher=Depends(get_password_hasher),
    token_generator=Depends(get_token_generator),
):
    logger.info(f"API Request: POST /auth/login: for email='{body.email}'")
    try:
        user = await LoginUser(repo, hasher).execute(body.email, body.password)
        access_token = token_generator.generate_token(user.id, user.email)
        
        # Set the HttpOnly Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,        # JavaScript cannot access it
            secure=True,          # Only sent over HTTPS
            samesite="lax",       # Protects against CSRF
            max_age=1440 * 60,    # 24 hours in seconds
            path="/",
        )
        
        logger.info(f"API Success: POST /auth/login logged in user email={user.email}")
        # Return user profile info (Zustand will store this)
        return {"id": str(user.id), "email": user.email}
    except ValueError as e:
        logger.warning(f"API Failure: POST /auth/login error: {e}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    except Exception as e:
        logger.error(f"API Error: POST /auth/login unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")


@router.post("/logout")
async def logout(response: Response):
    """clear the access token cookie"""
    response.delete_cookie(key="access_token", path="/")
    logger.info("User logged out, access token cookie cleared")
    return {"message": "Logged out successfully"}


# ── GitHub OAuth ──────────────────────────────────────────────────

@router.get("/github")
async def github_redirect(github=Depends(get_github_oauth)):
    """Step 1 — redirect browser to GitHub consent page."""
    logger.info("API Request: GET /auth/github redirecting user to GitHub consent page")
    state = secrets.token_urlsafe(16)   # store in session/cookie if you need CSRF check
    url = github.get_authorization_url(state)
    return RedirectResponse(url)

@router.get("/github/callback")
async def github_callback(
    code: str,
    response: Response, # 1. Inject Response object
    repo=Depends(get_auth_repo),
    github=Depends(get_github_oauth),
    token_generator=Depends(get_token_generator),
):
    """Step 2 — GitHub redirects back here with ?code=..."""
    logger.info("API Request: GET /auth/github/callback callback received from GitHub")
    try:
        user = await GitHubOAuthLogin(repo, github).execute(code)
        access_token = token_generator.generate_token(user.id, user.email)
        
        # 2. Set the HttpOnly Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1440 * 60,
            path="/",
        )
        
        logger.info(f"API Success: GET /auth/github/callback logged in user email='{user.email}' id='{user.id}'")
        # 3. Return user profile details instead of raw token in JSON
        return {"id": str(user.id), "email": user.email}
    except ValueError as e:
        logger.warning(f"API Failure: GET /auth/github/callback error: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.error(f"API Error: GET /auth/github/callback unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")


# ── Profile ────────────────────────────────────────────────────────

@router.get("/profile")
async def profile(user=Depends(get_current_user)):
    """Retrieve details of the currently authenticated user."""
    logger.info(f"API Request: GET /auth/profile for user email='{user.email}'")
    return {
        "id": str(user.id),
        "provider_user_id": user.provider_user_id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }