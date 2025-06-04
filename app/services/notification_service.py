from app.main.extensions import db
from app.models.notification import Notification
from app.models.user import User
from app.models.user_address import UserAddress

class NotificationService:
    @staticmethod
    def create_notification(user_id, event):
        n = Notification(user_id=user_id, event=event)
        db.session.add(n)
        db.session.commit()

    @staticmethod
    def notify_invitation(email, address_id):
        user = User.query.filter_by(email=email).first()
        if user and getattr(user, "notify_invites", True):
            NotificationService.create_notification(user.id, f"invited:{address_id}")

    @staticmethod
    def notify_resident_change(address_id, event, exclude_user_id=None):
        residents = UserAddress.query.filter_by(address_id=address_id).all()
        for r in residents:
            if exclude_user_id and r.user_id == exclude_user_id:
                continue
            if getattr(r.user, "notify_residents", True):
                NotificationService.create_notification(r.user_id, f"{event}:{address_id}")
