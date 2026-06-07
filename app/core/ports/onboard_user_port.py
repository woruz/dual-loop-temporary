from typing import Protocol

class IOnboardUser(Protocol):
    def execute(self, username: str, onboarding_description: str) -> None:
        """Triggered by the HTTP layer to register and onboard a user."""
        ...
