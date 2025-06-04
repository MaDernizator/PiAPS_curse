from app.main.extensions import db
from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def create_notification(user_id: int, event: str):
        notification = Notification(user_id=user_id, event=event)
        db.session.add(notification)
        db.session.commit()
        return {
            "id": notification.id,
            "user_id": user_id,
            "event": event,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None
        }

    @staticmethod
    def list_notifications(user_id: int):
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.sent_at.desc()).all()
        return [
            {
                "id": n.id,
                "event": n.event,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None
            }
            for n in notifications
        ]
