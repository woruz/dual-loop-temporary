from abc import ABC, abstractmethod

class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """
        Hash a plaintext password.
        """
        pass

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """
        Verify a plaintext password against a hash.
        """
        pass
