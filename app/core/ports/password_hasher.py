from typing import Protocol

class IPasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
    
    def verify(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""   