import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost/shop_search")
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    LOGO_PATH: str = os.getenv("LOGO_PATH", "")  # если не задан, используется заглушка
    SECRET_KEY: str = os.getenv("SECRET_KEY", "it-is-super-schearch-systems")

settings = Settings()

# Убедимся, что папка для загрузок существует
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
