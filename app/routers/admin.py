from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import Company, Product
from app.services.excel_loader import read_excel_preview, parse_excel_data
from app.config import settings
from app.dependencies import require_user
import os
import uuid


router = APIRouter(prefix="/admin", dependencies=[Depends(require_user)])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["settings"] = settings

# Список компаний
@router.get("/")
async def admin_root(request: Request, db: Session = Depends(get_db)):
    # return templates.TemplateResponse(request, "admin_menu.html")
    return RedirectResponse("/admin/companies")

@router.get("/companies")
async def companies_list(request: Request, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    return templates.TemplateResponse(request, "admin_companies.html", {"companies": companies})

# Добавление компании
@router.get("/companies/add")
async def add_company_form(request: Request):
    return templates.TemplateResponse(request, "admin_company_form.html", {"company": None})

@router.post("/companies/add")
async def add_company(request: Request, name: str = Form(...), phone: str = Form(""), email: str = Form(""), db: Session = Depends(get_db)):
    company = Company(name=name, phone=phone or None, email=email or None)
    try:
        db.add(company)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("admin_company_form.html", {
            "request": request,
            "company": None,
            "error": "Компания с таким наименованием уже существует"
        }, status_code=400)
    return RedirectResponse("/admin/companies", status_code=303)

# Редактирование компании
@router.get("/companies/{company_id}/edit")
async def edit_company_form(request: Request, company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return templates.TemplateResponse(request, "admin_company_form.html", {"company": company})

@router.post("/companies/{company_id}/edit")
async def edit_company(request: Request, company_id: int, name: str = Form(...), phone: str = Form(""), email: str = Form(""), db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.name = name
    company.phone = phone or None
    company.email = email or None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("admin_company_form.html", {
            "request": request,
            "company": company,
            "error": "Компания с таким наименованием уже существует"
        }, status_code=400)
    return RedirectResponse("/admin/companies", status_code=303)

# Удаление компании
@router.post("/companies/{company_id}/delete")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if company:
        db.delete(company)
        db.commit()
    return RedirectResponse("/admin/companies", status_code=303)

# Загрузка прайса - шаг 1 (форма)
@router.get("/companies/{company_id}/upload")
async def upload_form(request: Request, company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return templates.TemplateResponse(request, "admin_upload.html", {"company": company})

# Загрузка файла и предпросмотр
@router.post("/companies/{company_id}/upload/preview")
async def upload_preview(request: Request, company_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Сохраняем файл
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.xlsx', '.xls']:
        return templates.TemplateResponse(request, "admin_upload.html", {"company": company, "error": "Неверный формат файла. Допустимы .xlsx или .xls"}, status_code=400)
    temp_filename = f"{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(settings.UPLOAD_FOLDER, temp_filename)
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    # Читаем превью
    try:
        sheet_names, rows = read_excel_preview(temp_path)
    except Exception as e:
        os.remove(temp_path)
        return templates.TemplateResponse(request, "admin_upload.html", {"company": company, "error": f"Ошибка чтения файла: {str(e)}"}, status_code=400)
    # Определяем количество колонок (по максимальной строке)
    max_cols = max([len(r) for r in rows]) if rows else 0
    return templates.TemplateResponse(request, "admin_upload_preview.html", {
        "company": company,
        "temp_filename": temp_filename,
        "sheet_names": sheet_names,
        "rows": rows,
        "max_cols": max_cols,
        "total_rows": len(rows),
        "default_sheet": sheet_names[0] if sheet_names else ""
    })

# Обработка предпросмотра и загрузка данных
@router.post("/companies/{company_id}/upload/process")
async def upload_process(request: Request, company_id: int,
                         temp_filename: str = Form(...),
                         sheet_name: str = Form(...),
                         start_row: int = Form(...),
                         end_row: int = Form(...),
                         article_col: int = Form(...),
                         article_internal_col: int = Form(...),
                         price_col: int | None = Form(None),
                         price_cut_col: int | None = Form(None),
                         db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    temp_path = os.path.join(settings.UPLOAD_FOLDER, temp_filename)
    if not os.path.exists(temp_path):
        return templates.TemplateResponse(request, "admin_upload.html", {
            "company": company,
            "error": "Файл не найден, загрузите заново"
        }, status_code=400)

    try:
        products = parse_excel_data(
            temp_path, 
            sheet_name, 
            start_row, 
            end_row,
            article_col, 
            article_internal_col,
            price_col,
            price_cut_col)
    except ValueError as e:
        # Ошибка валидации (дубликаты и т.п.)
        try:
            os.remove(temp_path)
        except PermissionError:
            pass
        return templates.TemplateResponse(request, "admin_upload.html", {
            "company": company,
            "error": str(e)
        }, status_code=400)
    except Exception as e:
        # Любая другая ошибка обработки файла
        try:
            os.remove(temp_path)
        except PermissionError:
            pass
        return templates.TemplateResponse(request, "admin_upload.html", {
            "company": company,
            "error": f"Ошибка обработки файла: {str(e)}"
        }, status_code=400)

    # Если products успешно получена, удаляем старые товары
    db.query(Product).filter(Product.company_id == company_id).delete()
    for p in products:
        db.add(Product(
            article=p['article'], 
            article_internal=p['article_internal_col'],
            price=p['price'], 
            price_cut=p.get('price_cut'),
            company_id=company_id))
    db.commit()
    
    try:
        os.remove(temp_path)
    except PermissionError:
        pass

    return RedirectResponse("/admin/companies", status_code=303)
