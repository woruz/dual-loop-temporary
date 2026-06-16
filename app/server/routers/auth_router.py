
"""
LOCATION: app/server/routers/auth_router.py
 
WHY HERE: Routers handle HTTP concerns ONLY:
  - Parse request data
  - Call use-cases
  - Return HTTP responses / set cookies
 
They don't contain business logic. Think of them as a thin HTTP adapter
to your use-cases (same pattern as infrastructure, but for HTTP input).
 
CSRF STATE STORAGE:
  We use an HttpOnly cookie to store the OAuth state (CSRF token).
  Never store it in localStorage — XSS attacks can steal it.
  HttpOnly cookies are inaccessible to JavaScript.
"""
 
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
 
from app.core.use_cases.auth_use_cases import GithubAuthUseCase
from app.core.entities.user import User
from app.server.dependencies import get_auth_use_case, get_current_active_user
from app.server.auth_config import get_github_redirect_uri

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth",tags=["Authentication"])

import os 
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
 
 ##Response Schemas______________
class TokenResponse(BaseModel):
    access_token  : str
    refresh_token : str
    token_type : str = "bearer"
    expires_in : int

class UserResponse(BaseModel):
    id:int
    github_id:int
    github_username:str
    email:str
    github_url:str

    class Config:
        from_attributes = True

class RefreshRequest(BaseModel):
    refresh_token:str


class OAuthLoginUrlResponse(BaseModel):
    authorization_url: str
    state: str
    callback_url: str
    instructions: str = (
        "Open authorization_url in a browser tab (not Swagger). "
        "After GitHub login, copy access_token from the redirect URL "
        "and use Swagger Authorize with: Bearer <access_token>"
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.get(
    "/github/login/url",
    response_model=OAuthLoginUrlResponse,
    summary="Get GitHub OAuth URL (Swagger-friendly)",
)
async def github_login_url(
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
):
    """
    Returns the GitHub authorization URL as JSON.

    Use this from Swagger instead of /auth/github/login — Swagger cannot
    follow 302 redirects to external sites like github.com.
    """
    redirect_uri = get_github_redirect_uri()
    url, state = auth_use_case.get_ouauth_url()
    logger.info(
        "OAuth login URL generated | redirect_uri=%s | callback_url=%s",
        redirect_uri,
        redirect_uri,
    )
    return OAuthLoginUrlResponse(
        authorization_url=url,
        state=state,
        callback_url=redirect_uri,
    )


@router.get(
    "/github/login",
    summary="Initiate GitHub OAuth flow (browser redirect)",
    responses={302: {"description": "Redirect to GitHub — open in browser, not Swagger"}},
)
async def github_login(
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
):
    """    
    Step 1: Redirect user to GitHub for authentication.
 
    Flow:
      Browser → GET /auth/github/login
      → Server generates state (CSRF token), stores in cookie
      → Redirect to GitHub with client_id + state
      → GitHub shows "Authorize" page
    """
    url, state = auth_use_case.get_ouauth_url()
    logger.info("Redirecting browser to GitHub OAuth: %s", url)
    response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=600,
        path="/auth",
    )

    logger.info("Redirecting user to Github Oauth")
    return response

@router.get("/github/callback", summary="GitHub OAuth callback")
async def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    oauth_state: Optional[str] = Cookie(default=None),
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
):
    """
    Step 2: GitHub redirects here after user approves access.
 
    GitHub sends: ?code=xxx&state=yyy
    We verify state matches our cookie (CSRF check), then exchange code for token.
 
    On success: Redirects to frontend with tokens in URL fragment (#)
    On failure: Redirects to frontend with error
    """

    logger.info("OAuth callback received | redirect_uri=%s", get_github_redirect_uri())

    if error:
        logger.error("GitHub OAuth error: %s — %s", error, error_description)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error={error}",
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        logger.warning("OAuth callback missing code or state")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error=missing_code",
            status_code=status.HTTP_302_FOUND,
        )

    ##CSRF Validation
    if not oauth_state:
        logger.warning("OAuth callback received with no state cookie")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error=missing_state",
            status_code=status.HTTP_302_FOUND,
        )
    try:
        tokens, user = await auth_use_case.handle_callback(
            code=code,
            state=state,
            expected_state=oauth_state,
        )
    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error=oauth_failed",
            status_code=status.HTTP_302_FOUND,
        )
    
    # Clear the one-time CSRF cookie
    response = RedirectResponse(
        url=(
            f"{FRONTEND_URL}/auth/success"
            f"?access_token={tokens.access_token}"
            f"&refresh_token={tokens.refresh_token}"
            f"&token_type={tokens.token_type}"
        ),
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie("oauth_state", path="/auth")
 
    logger.info(f"OAuth callback successful for user: {user.github_username}")
    return response

@router.post("/github/callback/json", response_model=TokenResponse, summary="GitHub OAuth (JSON API)")
async def github_callback_json(
    code:str,
    state:str,
      expected_state: str,
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
):
    """
    Alternative callback for SPA/mobile apps that can't use cookie-based CSRF.
    The client manages state verification themselves.
 
    Usage: POST /auth/github/callback/json?code=xxx&state=yyy&expected_state=yyy
    """
    try:
        tokens, _user = await auth_use_case.handle_callback(
            code=code,
            state=state,
            expected_state=expected_state,
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    body:RefreshRequest,
    auth_use_case:GithubAuthUseCase = Depends(get_auth_use_case)

):
    
    """
    Exchange a valid refresh token for new access + refresh tokens.
    Call this when API returns 401 and you have a refresh token stored.
    """

    try:
        tokens = await auth_use_case.refresh_tokens(body.refresh_token)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    
 
@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Protected endpoint — requires Authorization: Bearer <access_token>
    Returns the currently authenticated user's profile.
    """
    return UserResponse(
        id=current_user.id,
        github_id=current_user.github_id,
        github_username=current_user.github_username,
        email=current_user.email,
        github_url=current_user.github_url,
    )
 


