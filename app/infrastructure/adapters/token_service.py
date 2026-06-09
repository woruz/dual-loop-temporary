"""
LOCATION: app/infrastructure/adapters/token_service.py
 
WHY HERE: JWT creation/verification is infrastructure — it depends on
the python-jose library. Use-cases only know about the TokenServicePort interface.
 
WHY TWO TOKENS:
  Access token (30 min): Short-lived, sent with every API request.
                          If stolen, damage is limited by expiry.
  Refresh token (7 days): Long-lived, only sent to /auth/refresh endpoint.
                           Used to get new access tokens without re-login.
"""
from datetime import datetime 
from typing import Optional
import os
import logging
from jose import JWTError,jwt
from app.core.ports.auth_ports import TokenServicePort

logger = logging.getLogger(__name__)

# Token "purpose" claims — prevents using an access token as a refresh token
ACCESS_TOKEN_PURPOSE = "access"
REFRESH_TOKEN_PURPOSE = "refresh"

class JWTTokenService(TokenServicePort):
        """
    Implements JWT creation and verification using python-jose.
    Uses HS256 (HMAC SHA-256) — suitable for single-server apps.
    For multi-service, consider RS256 (asymmetric).
    """
        def __init__(self):
                self.secret_key = os.getenv("SECRETKEY","")
                self.algorithm = os.getenv("ALGORITHM","HS256")
                self.acess_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
                self.refresh_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS","7"))
                
