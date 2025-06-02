from app.main.extensions import db
from sqlalchemy import Enum
from sqlalchemy.orm import relationship
from app.models.enums import ResidentRole

class UserAddress(db.Model):
    __tablename__ = "user_addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)
    role = db.Column(Enum(ResidentRole), nullable=False, default=ResidentRole.RESIDENT)

    user = relationship("User", back_populates="addresses")
    address = relationship("Address", back_populates="residents")
