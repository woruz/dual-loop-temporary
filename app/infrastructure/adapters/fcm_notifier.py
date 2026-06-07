from app.core.ports import INotificationDispatcher

class FCMNotifier:  # Note: implements INotificationDispatcher structurally
    def send_divergence_alert(self, user_id: str, score: float) -> None:
        print(f"[Adapter] FCMNotifier ALERT: User {user_id} has high daily divergence score of {score}!")
