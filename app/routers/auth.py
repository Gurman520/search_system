from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, LoginHistory
from app.services.auth import verify_password
from app.services.brute_force import is_blocked, register_failure, clear_failures
from app.config import settings


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["settings"] = settings

@router.get("/login")
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None, "login_value": ""})

@router.post("/login")
async def login_submit(request: Request,
                       login: str = Form(...),
                       password: str = Form(...),
                       db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)

    login = login.strip()
    ip = request.client.host if request.client else "unknown"
    user_agent = (request.headers.get("user-agent") or "")[:500]
    key = f"{login}:{ip}"

    if is_blocked(key):
        return templates.TemplateResponse(request, "login.html", {
            "error": "Слишком много неудачных попыток входа. Попробуйте через 15 минут.",
            "login_value": login
        }, status_code=429)

    user = db.query(User).filter(User.login == login).first()
    success = bool(user and verify_password(password, user.password_hash))

    db.add(LoginHistory(
        user_id=user.id if user else None,
        login_attempted=login,
        ip_address=ip,
        user_agent=user_agent,
        success=success,
    ))
    db.commit()

    if not success:
        register_failure(key)
        return templates.TemplateResponse(request, "login.html", {
            "error": "Неверный логин или пароль",
            "login_value": login
        }, status_code=401)

    clear_failures(key)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
