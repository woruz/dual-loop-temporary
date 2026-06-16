
"""
LOCATION: app/main.py  (root of the app package)
 
This is the FastAPI app factory. It:
  1. Creates the app instance
  2. Configures CORS
  3. Registers all routers
  4. Wires startup/shutdown events (DB table creation)
  5. Adds global exception handling
"""
 
import logging

from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.infrastructure.adapters.database import create_tables
from app.infrastructure.adapters.journal_models import create_journal_tables
from app.infrastructure.adapters.repository_models import create_repository_tables
from app.server.routers.auth_router import router as auth_router
from app.server.routers.journal_router import router as journal_router
from app.server.routers.repository_router import router as repository_router
from app.server.auth_config import log_oauth_startup_config

##Loggin setup____________________________________
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL","INFO")),format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",)
logger = logging.getLogger(__name__)

# ─── Lifespan (startup + shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app:FastAPI):
    """Runs on startup and shutdown."""
    logger.info("Starting up Dualoop API...")
    log_oauth_startup_config()
    await create_tables()
    await create_journal_tables()
    await create_repository_tables()
    logger.info("Database tables verified/created")
    yield
    logger.info("Shutting down Dualoop API")


app = FastAPI(
    lifespan=lifespan,
    title="Dualoop API",
    description="GitHub OAuth + Daily Journal Analysis API",
    version="1.0.0",
)

# CORS on the module-level app (used by uvicorn main:app)
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste the access_token from /auth/github/login/url or OAuth callback",
        }
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
 
##App Factory___________________
def create_app()->FastAPI:
    app = FastAPI(
        title="Dualoop API",
        description="GitHub OAuth authentication service",
        version="1.0.0",
        lifespan=lifespan,
        # Disable docs in production for security
        docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    )
      # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")
 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins],
        allow_credentials=True,   # Required for cookies (OAuth state)
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    ##Global Acess handler______________________
    @app.exception_handler(Exception)
    async def global_exception_handler(request:Request,exc:Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    app.include_router(auth_router, prefix="api/v1")
    app.include_router(journal_router, prefix="/api/v1")
    app.include_router(repository_router, prefix="/api/v1")
    ##Health Check________________
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok", "environment": os.getenv("ENVIRONMENT", "development")}
 
    return app
 

app.include_router(auth_router)
app.include_router(journal_router, prefix="/api/v1")
app.include_router(repository_router, prefix="/api/v1")

  

    
