import bcrypt
import logging
from app.core.ports.password_hasher import IPasswordHasher

logger = logging.getLogger("app.infrastructure.adapters.bcrypt_hasher")

class BcryptHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        logger.debug("Hashing password...")
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_bytes.decode('utf-8')

    def verify(self, password: str, hashed: str) -> bool:
        try:
            logger.debug("Verifying password...")
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {e}", exc_info=True)
            return False
