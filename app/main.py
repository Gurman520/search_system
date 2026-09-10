from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import traceback
from contextlib import asynccontextmanager
from app.routers import pages, admin, auth, admin_users
from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.dependencies import NotAuthenticated
from app.services.auth import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание superuser при старте
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.login == "superuser").first():
            db.add(User(
                first_name="Super",
                last_name="User",
                login="superuser",
                password_hash=hash_password("l137784"),
                is_superuser=True,
            ))
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="Shop Product Search", lifespan=lifespan)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Шаблоны с глобальной переменной settings
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
templates.env.globals["settings"] = settings

# Middleware: подгружаем пользователя в request.state для шаблонов
@app.middleware("http")
async def load_user_middleware(request: Request, call_next):
    request.state.user = None
    session = getattr(request, "session", None)
    if session:
        uid = session.get("user_id")
        if uid:
            db = SessionLocal()
            try:
                request.state.user = db.get(User, uid)
            finally:
                db.close()
    return await call_next(request)

# SessionMiddleware должен быть добавлен ПОСЛЕ load_user, чтобы быть outer
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, max_age=60 * 60 * 24 * 7)

# Доверяем заголовкам от Nginx (внутри docker-сети)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Обработчик NotAuthenticated → редирект на /login
@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)

# Регистрируем обработчик HTTP-ошибок
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Для 500-й ошибки показываем кастомную страницу
    if exc.status_code == 500:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": 500,
                "error_message": str(exc.detail) if exc.detail else "Внутренняя ошибка сервера"
            },
            status_code=500
        )
    # Для остальных HTTP-ошибок также можно показывать кастомную страницу
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "error_message": str(exc.detail) if exc.detail else "Ошибка запроса"
        },
        status_code=exc.status_code
    )

# Регистрируем обработчик всех необработанных исключений (500)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Логируем ошибку в консоль для отладки
    print("Unhandled exception:")
    traceback.print_exc()
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": 500,
            "error_message": str(exc) if str(exc) else "Неизвестная ошибка"
        },
        status_code=500
    )

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(admin_users.router)
