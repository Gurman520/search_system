from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('company_id', 'article', name='uq_company_article'),
    )

    id = Column(Integer, primary_key=True, index=True)
    article = Column(String(255), nullable=False, index=True)
    article_internal = Column(String(255), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    price_cut = Column(Numeric(10, 2), nullable=True)

    company = relationship("Company", back_populates="products")
    