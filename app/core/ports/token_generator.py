from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ITokenGenerator(ABC):
    @abstractmethod
    def generate_token(self, user_id: str, email: str, is_verified_forjournal: bool = False) -> str:
        """
        Generate a token for a given user.
        """
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify the given token and return its payload if valid, otherwise None.
        """
        pass
