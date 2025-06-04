import uuid
from datetime import datetime
from app.main.extensions import db
from app.models.invitation import Invitation
from app.models.user import User
from app.models.address import Address
from app.models.user_address import UserAddress
from app.models.enums import ResidentRole
from app.models.enums import UserRole
from app.services.notification_service import NotificationService

class InvitationService:

    @staticmethod
    def create_invitation(data, inviter_id):
        target_email = data["target_email"]
        address_id = data["address_id"]

        address = Address.query.get(address_id)
        if not address:
            raise ValueError("Address not found")

        owner_link = UserAddress.query.filter_by(
            address_id=address_id,
            user_id=inviter_id,
            role=ResidentRole.OWNER
        ).first()

        if not owner_link:
            raise ValueError("Only OWNER can invite users to this address")

        target_user = User.query.filter_by(email=target_email).first()
        if not target_user:
            raise ValueError("Target user does not exist")

        # уже приглашён?
        existing = Invitation.query.filter_by(
            address_id=address_id,
            email=target_email,
            used=False
        ).first()
        if existing:
            raise ValueError("User already invited")

        invitation = Invitation(
            email=target_email,
            address_id=address_id,
            code=str(uuid.uuid4())[:8],
            created_at=datetime.utcnow(),
            used=False
        )
        db.session.add(invitation)
        db.session.commit()

        NotificationService.notify_invitation(target_user.email, address_id, inviter_id, invitation.id)

        return {"invitation_code": invitation.code}

    @staticmethod
    def accept_invitation(code, user_id):
        user = User.query.get(user_id)
        invitation = Invitation.query.filter_by(code=code, used=False).first()
        if not invitation or invitation.email != user.email:
            raise ValueError("Invitation not found or not for you")

        # уже добавлен?
        exists = UserAddress.query.filter_by(
            user_id=user_id,
            address_id=invitation.address_id
        ).first()
        if exists:
            raise ValueError("Already associated with address")

        # добавить жильца
        user_address = UserAddress(
            user_id=user_id,
            address_id=invitation.address_id,
            role=ResidentRole.GUEST
        )
        db.session.add(user_address)
        db.session.delete(invitation)
        db.session.commit()

        NotificationService.notify_resident_change(
            invitation.address_id,
            "resident_added",
            exclude_user_id=user_id
        )
