import uuid
from app.main.extensions import db
from app.models.invitation import Invitation
from app.models.user import User
from app.models.address import Address
from app.models.user_address import UserAddress
from app.models.enums import ResidentRole
from app.models.enums import UserRole

class InvitationService:

    @staticmethod
    def create_invitation(data, inviter_id):
        target_email = data["target_email"]
        target_role = data["target_role"]
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
            target_user_id=target_user.id
        ).first()
        if existing:
            raise ValueError("User already invited")

        invitation = Invitation(
            code=str(uuid.uuid4())[:8],
            inviter_user_id=inviter_id,
            target_user_id=target_user.id,
            address_id=address_id,
            target_role=ResidentRole[target_role]
        )
        db.session.add(invitation)
        db.session.commit()

        return {"invitation_code": invitation.code}

    @staticmethod
    def accept_invitation(code, user_id):
        invitation = Invitation.query.filter_by(code=code, target_user_id=user_id).first()
        if not invitation:
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
            role=invitation.target_role
        )
        db.session.add(user_address)
        db.session.delete(invitation)
        db.session.commit()
