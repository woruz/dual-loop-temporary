from typing import Protocol, List

class IIdentityEncoder(Protocol):
    def encode(self, text: str) -> List[float]:
        """Encodes a text string into a list of floats (embedding vector)."""
        ...
