import bcrypt

from app.core.ports.password_hasher import IPasswordHasher

class BcryptHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except (ValueError, TypeError):
            return False