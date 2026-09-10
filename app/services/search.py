from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Product, Company

def search_products(db: Session, article: str, company_id: int | None = None, limit: int = 100):
    query = db.query(Product, Company).join(Company, Product.company_id == Company.id)
    # Поиск по частичному совпадению без учёта регистра
    query = query.filter(
        or_(
            Product.article.ilike(f"%{article}%"),
            Product.article_internal.ilike(f"%{article}%")
            )
    )
    if company_id:
        query = query.filter(Product.company_id == company_id)
    results = query.order_by(Product.article, Product.article_internal).limit(limit).all()
    return results  # список кортежей (Product, Company)
