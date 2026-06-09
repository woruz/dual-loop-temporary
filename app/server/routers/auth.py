import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.server.dependencies import (
    get_auth_repo,
    get_github_oauth,
    get_password_hasher,
    get_token_generator
)
from app.core.use_cases.register_user import RegisterUser
from app.core.use_cases.login_user import LoginUser
from app.core.use_cases.github_oauth_login import GitHubOAuthLogin

logger = logging.getLogger("app.server.routers.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

class EmailPasswordBody(BaseModel):
    email: EmailStr
    password: str

# ── Email / Password ──────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: EmailPasswordBody,
    repo=Depends(get_auth_repo),
    hasher=Depends(get_password_hasher),
    token_generator=Depends(get_token_generator),
):
    logger.info(f"API Request: POST /auth/register for email='{body.email}'")
    try:
        user = await RegisterUser(repo, hasher).execute(body.email, body.password)
        access_token = token_generator.generate_token(user.id, user.email)
        logger.info(f"API Success: POST /auth/register registered user email='{user.email}' id='{user.id}'")
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        logger.warning(f"API Failure: POST /auth/register error: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.error(f"API Error: POST /auth/register unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")


@router.post("/login")
async def login(
    body: EmailPasswordBody,
    repo=Depends(get_auth_repo),
    hasher=Depends(get_password_hasher),
    token_generator=Depends(get_token_generator),
):
    logger.info(f"API Request: POST /auth/login for email='{body.email}'")
    try:
        user = await LoginUser(repo, hasher).execute(body.email, body.password)
        access_token = token_generator.generate_token(user.id, user.email)
        logger.info(f"API Success: POST /auth/login logged in user email='{user.email}' id='{user.id}'")
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        logger.warning(f"API Failure: POST /auth/login error: {e}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    except Exception as e:
        logger.error(f"API Error: POST /auth/login unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")


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
    repo=Depends(get_auth_repo),
    github=Depends(get_github_oauth),
    token_generator=Depends(get_token_generator),
):
    """Step 2 — GitHub redirects back here with ?code=..."""
    logger.info("API Request: GET /auth/github/callback callback received from GitHub")
    try:
        user = await GitHubOAuthLogin(repo, github).execute(code)
        access_token = token_generator.generate_token(user.id, user.email)
        logger.info(f"API Success: GET /auth/github/callback logged in user email='{user.email}' id='{user.id}'")
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        logger.warning(f"API Failure: GET /auth/github/callback error: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.error(f"API Error: GET /auth/github/callback unexpected error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred.")