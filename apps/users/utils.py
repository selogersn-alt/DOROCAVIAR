from .models import Notification

def create_notification(recipient, sender, notification_type, text, link=""):
    """Utilitaire pour créer une notification."""
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        text=text,
        link=link
    )
