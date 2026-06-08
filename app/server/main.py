from app.server.logging_config import setup_logging

# Configure logging FIRST
setup_logging()

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)
from app.infrastructure.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing app and starting up Dual Loop server...")
    yield
    logger.info("Shutting down Dual Loop server...")

app = FastAPI(
    title="Dual Loop Server",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    logger.info("Root endpoint hit")
    return {"message": "Dual Loop server is running"}
    
