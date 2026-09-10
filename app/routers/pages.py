from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Company
from app.services.search import search_products
from app.config import settings
from app.dependencies import require_user


router = APIRouter(dependencies=[Depends(require_user)])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["settings"] = settings

@router.get("/")
async def index(request: Request, company_id: str | None = None, article: str | None = None, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    results = []
    message = None
    company_id_int = None
    if company_id and company_id.strip():
        try:
            company_id_int = int(company_id)
        except ValueError:
            company_id_int = None  # или можно показать сообщение


    if article and len(article) >= 4:
        results = search_products(db, article, company_id_int)
        if len(results) == 100:
            message = "Показаны первые 100 результатов. Уточните запрос для более полного вывода."
        elif not results:
            message = "Ничего не найдено."
    elif article and len(article) < 4:
        message = "Введите не менее 4 символов для поиска."

    return templates.TemplateResponse(request, "index.html", {
        "companies": companies,
        "selected_company": company_id_int,
        "article": article or "",
        "results": results,
        "message": message
    })
