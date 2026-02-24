from sqlalchemy import Column, Integer, String, Boolean, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    
    description = Column(String(1000), nullable=True)

    price = Column(Numeric(10, 2), nullable=False)

    stock = Column(Integer, default=0, nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")