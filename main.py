
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
from app.server.routers.auth_router import router as auth_router


app = FastAPI()

##Loggin setup____________________________________
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL","INFO")),format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",)
logger = logging.getLogger(__name__)

# ─── Lifespan (startup + shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app:FastAPI):
    """Runs on startup and shutdown."""
    logger.info("Starting up Dualoop API...")
    await create_tables()
    logger.info("Database tables verified/created")
    yield
    logger.info("Shutting down Dualoop API")
 
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
    ##Health Check________________
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok", "environment": os.getenv("ENVIRONMENT", "development")}
 
    return app
 

app.include_router(auth_router)

  

    
