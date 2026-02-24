import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False, index=True)

    hashed_password = Column(String, nullable=False)

    role = Column(
        Enum(UserRole),
        default=lambda: UserRole.user,
        server_default=UserRole.user.value,
        nullable=False
    )

    phone = Column(String(20), nullable=True)

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")