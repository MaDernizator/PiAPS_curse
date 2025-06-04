from app.main.extensions import db
from app.models.notification import Notification
from app.models.user import User
from app.models.user_address import UserAddress

class NotificationService:
    @staticmethod
    def create_notification(user_id, event, viewed=False):
        n = Notification(user_id=user_id, event=event, viewed=viewed)
        db.session.add(n)
        db.session.commit()

    @staticmethod
    def notify_invitation(email, address_id, inviter_id, invitation_id):
        user = User.query.filter_by(email=email).first()
        if user:
            viewed = not getattr(user, "notify_invites", True)
            event = f"invited:{address_id}:{inviter_id}:{invitation_id}"
            NotificationService.create_notification(user.id, event, viewed=viewed)

    @staticmethod
    def notify_resident_change(address_id, event, exclude_user_id=None):
        residents = UserAddress.query.filter_by(address_id=address_id).all()
        for r in residents:
            if exclude_user_id and r.user_id == exclude_user_id:
                continue
            viewed = not getattr(r.user, "notify_residents", True)
            NotificationService.create_notification(r.user_id, f"{event}:{address_id}", viewed=viewed)
