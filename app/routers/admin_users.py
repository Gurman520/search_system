from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, LoginHistory
from app.services.auth import hash_password, validate_password, generate_login
from app.dependencies import require_user
from app.config import settings


router = APIRouter(prefix="/admin/users", dependencies=[Depends(require_user)])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["settings"] = settings

@router.get("")
async def users_list(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(request, "admin_users.html", {"users": users})

@router.get("/add")
async def add_user_form(request: Request):
    return templates.TemplateResponse(request, "admin_user_form.html", {"user_obj": None, "error": None})

@router.post("/add")
async def add_user(request: Request,
                   first_name: str = Form(...),
                   last_name: str = Form(...),
                   login: str = Form(""),
                   password: str = Form(...),
                   db: Session = Depends(get_db)):
    first_name = first_name.strip()
    last_name = last_name.strip()
    login = login.strip()

    if not first_name or not last_name or not password:
        return templates.TemplateResponse(request, "admin_user_form.html", {
            "user_obj": None, "error": "Все поля обязательны для заполнения"
        }, status_code=400)

    if not login:
        login = generate_login(first_name, last_name)
        if not login:
            return templates.TemplateResponse(request, "admin_user_form.html", {
                "user_obj": None, "error": "Не удалось сгенерировать логин. Укажите вручную."
            }, status_code=400)
        base = login
        i = 1
        while db.query(User).filter(User.login == login).first():
            login = f"{base}{i}"
            i += 1

    if db.query(User).filter(User.login == login).first():
        return templates.TemplateResponse(request, "admin_user_form.html", {
            "user_obj": None, "error": f"Логин '{login}' уже занят"
        }, status_code=400)

    ok, err = validate_password(password)
    if not ok:
        return templates.TemplateResponse(request, "admin_user_form.html", {
            "user_obj": None, "error": err
        }, status_code=400)

    db.add(User(
        first_name=first_name,
        last_name=last_name,
        login=login,
        password_hash=hash_password(password),
    ))
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/{user_id}/edit")
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return templates.TemplateResponse(request, "admin_user_form.html", {"user_obj": user, "error": None})

@router.post("/{user_id}/edit")
async def edit_user(request: Request, user_id: int,
                    first_name: str = Form(...),
                    last_name: str = Form(...),
                    login: str = Form(...),
                    password: str = Form(""),
                    db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    first_name = first_name.strip()
    last_name = last_name.strip()
    login = login.strip()

    if not first_name or not last_name or not login:
        return templates.TemplateResponse(request, "admin_user_form.html", {
            "user_obj": user, "error": "Все поля кроме пароля обязательны"
        }, status_code=400)

    existing = db.query(User).filter(User.login == login, User.id != user_id).first()
    if existing:
        return templates.TemplateResponse(request, "admin_user_form.html", {
            "user_obj": user, "error": f"Логин '{login}' уже занят"
        }, status_code=400)

    if password:
        ok, err = validate_password(password)
        if not ok:
            return templates.TemplateResponse(request, "admin_user_form.html", {
                "user_obj": user, "error": err
            }, status_code=400)
        user.password_hash = hash_password(password)

    user.first_name = first_name
    user.last_name = last_name
    user.login = login
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/{user_id}/delete")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user and not user.is_superuser:
        db.delete(user)
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/{user_id}/history")
async def user_history(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    history = (db.query(LoginHistory)
               .filter(LoginHistory.user_id == user_id)
               .order_by(LoginHistory.login_at.desc())
               .limit(200).all())
    return templates.TemplateResponse(request, "admin_user_history.html", {"user_obj": user, "history": history})
