from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    