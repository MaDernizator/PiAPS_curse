import uuid
from app.main.extensions import db
from app.models.address import Address
from app.models.user_address import UserAddress
from app.models.enums import ResidentRole

class AddressService:

    @staticmethod
    def create_address(data, owner_id):
        address = Address(
            street=data["street"],
            building_number=data["building_number"],
            unit_number=data["unit_number"],
            owner_code=str(uuid.uuid4())[:8]  # короткий уникальный код
        )
        db.session.add(address)
        db.session.commit()

        # связываем владельца
        user_address = UserAddress(
            user_id=owner_id,
            address_id=address.id,
            role=ResidentRole.OWNER
        )
        db.session.add(user_address)
        db.session.commit()

        return {
            "id": address.id,
            "street": address.street,
            "building_number": address.building_number,
            "unit_number": address.unit_number,
            "owner_code": address.owner_code
        }

    @staticmethod
    def list_user_addresses(user_id):
        results = UserAddress.query.filter_by(user_id=user_id).all()
        return [
            {
                "id": ua.address.id,
                "street": ua.address.street,
                "building_number": ua.address.building_number,
                "unit_number": ua.address.unit_number,
                "role": ua.role.value
            }
            for ua in results
        ]

    @staticmethod
    def join_by_code(user_id, code):
        address = Address.query.filter_by(owner_code=code).first()
        if not address:
            raise ValueError("Invalid owner code")

        # уже присоединён?
        exists = UserAddress.query.filter_by(user_id=user_id, address_id=address.id).first()
        if exists:
            raise ValueError("Already associated with this address")

        user_address = UserAddress(
            user_id=user_id,
            address_id=address.id,
            role=ResidentRole.RESIDENT
        )
        db.session.add(user_address)
        db.session.commit()

        return {
            "id": address.id,
            "street": address.street,
            "building_number": address.building_number,
            "unit_number": address.unit_number,
        }
