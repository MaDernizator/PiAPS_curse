from app.main.extensions import db
from sqlalchemy.orm import relationship

class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(120), nullable=False)
    building_number = db.Column(db.String(20), nullable=False)
    unit_number = db.Column(db.String(20), nullable=False)
    owner_code = db.Column(db.String(16), unique=True, nullable=False)

    residents = relationship("UserAddress", back_populates="address", cascade="all, delete-orphan")
    invitations = db.relationship("Invitation", back_populates="address", cascade="all, delete-orphan")


