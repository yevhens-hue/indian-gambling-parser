"""Конфигурация приложения"""
import os
from pathlib import Path

# Корневая директория проекта (3 уровня вверх от этого файла)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Путь к БД
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "providers_data.db"))
XLSX_PATH = os.getenv("XLSX_PATH", str(BASE_DIR / "providers_data.xlsx"))

# Google Sheets (опционально)
# ID таблицы из URL: https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", str(BASE_DIR / "google_credentials.json"))

# CORS настройки
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Путь к скриншотам
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Настройки API
API_PREFIX = "/api"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Авторизация (в продакшене использовать переменные окружения!)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-use-env-var")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
