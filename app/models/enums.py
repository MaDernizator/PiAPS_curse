import enum

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class ResidentRole(enum.Enum):
    OWNER = "OWNER"
    GUEST = "GUEST"
    RESIDENT = "RESIDENT"
