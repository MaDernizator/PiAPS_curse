from app.main.extensions import db
from app.models.user_address import UserAddress
from app.models.enums import ResidentRole
from app.services.notification_service import NotificationService

class ResidentService:

    @staticmethod
    def _check_owner(user_id, address_id):
        owner = UserAddress.query.filter_by(
            user_id=user_id,
            address_id=address_id,
            role=ResidentRole.OWNER
        ).first()
        if not owner:
            raise ValueError("You are not the owner of this address")

    @staticmethod
    def list_residents(user_id, address_id):
        ResidentService._check_owner(user_id, address_id)

        residents = UserAddress.query.filter_by(address_id=address_id).all()
        return [
            {
                "user_id": r.user.id,
                "name": r.user.name,
                "email": r.user.email,
                "role": r.role.value
            }
            for r in residents
        ]

    @staticmethod
    def block_resident(user_id, address_id, target_user_id):
        ResidentService._check_owner(user_id, address_id)

        target = UserAddress.query.filter_by(
            address_id=address_id,
            user_id=target_user_id
        ).first()

        if not target:
            raise ValueError("User not found in this address")

        db.session.delete(target)
        db.session.commit()

        NotificationService.notify_resident_change(
            address_id,
            "resident_removed",
            exclude_user_id=target_user_id,
        )

    @staticmethod
    def update_role(user_id, address_id, target_user_id, new_role):
        ResidentService._check_owner(user_id, address_id)

        target = UserAddress.query.filter_by(
            address_id=address_id,
            user_id=target_user_id
        ).first()

        if not target:
            raise ValueError("User not found in this address")

        target.role = ResidentRole[new_role]
        db.session.commit()

        NotificationService.notify_resident_change(
            address_id,
            "role_changed",
            exclude_user_id=target_user_id,
        )
#TODO сейчас может быть два овнера, подумать