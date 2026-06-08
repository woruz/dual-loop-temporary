import loggingimport logging
from fastapi import APIRouter, status
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)