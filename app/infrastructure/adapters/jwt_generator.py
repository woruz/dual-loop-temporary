import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from app.core.ports.token_generator import ITokenGenerator

logger = logging.getLogger("app.infrastructure.adapters.jwt_generator")

class JWTGenerator(ITokenGenerator):
    def __init__(self):
        # Read JWT_SECRET from .env, fallback to a secure randomly generated token for development
        self.secret_key = os.getenv("JWT_SECRET", "fallback_secret_key_change_me_in_production_jwt")
        self.algorithm = "HS256"
        self.expire_minutes = 1440  # 24 hours
        logger.debug(f"JWTGenerator initialized with algorithm {self.algorithm}")

    def generate_token(self, user_id: Any, email: str) -> str:
        logger.info(f"Generating access token for user: {email} (id: {user_id})")
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            logger.debug("Verifying access token...")
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected token verification error: {e}", exc_info=True)
            return None
