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
from datetime import datetime, timedelta, timezone
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
     def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        if not self.secret_key or self.secret_key == "your-secret-key-change-in-production":
            if os.getenv("ENVIRONMENT") == "production":
                raise RuntimeError("SECRET_KEY must be set to a secure value in production!")
            if not self.secret_key:
                self.secret_key = "dev-insecure-key-change-me"
            logger.warning("Using insecure SECRET_KEY — change for production!")
    
     def _create_token(
        self,
        subject:str,
        purpose:str,
        expire_delta: timedelta,
        extra_claims: Optional[dict] = None,


    )-> str:
         now = datetime.now(timezone.utc)
         payload = {
             "sub": subject,
             "purpose": purpose,
             "iat": int(now.timestamp()),
             "exp": int((now + expire_delta).timestamp()),
             **(extra_claims or {}),
         }
         return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
     def _verify_token(self,token:str,expected_purpose:str)-> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")
 
        # Check it's the right type of token
        if payload.get("purpose") != expected_purpose:
            raise ValueError(
                f"Wrong token type: expected '{expected_purpose}', "
                f"got '{payload.get('purpose')}'"
            )
        return payload
     def create_access_token(self, user_id: int, username: str) -> str:
        return self._create_token(
            subject=str(user_id),
            purpose=ACCESS_TOKEN_PURPOSE,
            expire_delta=timedelta(minutes=self.access_expire_minutes),
            extra_claims={"username": username},
        )
     def create_refresh_token(self, user_id:int) -> str:
         return self._create_token(subject=str(user_id),purpose=REFRESH_TOKEN_PURPOSE,expire_delta=timedelta(days=self.refresh_expire_days))
     def verify_access_token(self, token: str) -> dict:
        return self._verify_token(token, ACCESS_TOKEN_PURPOSE)
 
     def verify_refresh_token(self, token: str) -> dict:
          return self._verify_token(token, REFRESH_TOKEN_PURPOSE)
 
     
         