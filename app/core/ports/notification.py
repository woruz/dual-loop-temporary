from typing import Protocol

class INotificationDispatcher(Protocol):
    def send_divergence_alert(self, user_id: str, score: float) -> None:
        """Sends a push notification alert (FCM) when divergence is too high."""
        ...
