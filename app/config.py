import os
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "some-super-secret-key")  # 👈 добавь
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/komuservice")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")