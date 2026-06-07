from typing import List
from app.core.ports import IIdentityEncoder

class ONNXEncoder:  # Note: implements IIdentityEncoder structurally
    def encode(self, text: str) -> List[float]:
        print(f"[Adapter] ONNXEncoder encoding: '{text}'")
        # Return a dummy 384-dimensional embedding vector (all-MiniLM size)
        return [0.1] * 384
