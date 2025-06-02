from app.main.extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
from app.models.enums import UserRole
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
