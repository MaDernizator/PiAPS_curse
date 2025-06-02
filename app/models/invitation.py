from app.main.extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
from app.models.enums import ResidentRole

class Invitation(db.Model):
    __tablename__ = "invitations"

    id = db.Column(db.Integer, primary_key=True)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)
    inviter_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # может быть null, если приглашение ещё не принято
    target_role = db.Column(Enum(ResidentRole), nullable=False)

    address = relationship("Address", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_user_id])
    target = relationship("User", foreign_keys=[target_user_id])
