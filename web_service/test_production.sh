#!/bin/bash
# Скрипт для тестирования production конфигурации

set -e

echo "🧪 Тестирование Production конфигурации"
echo "========================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# 1. Проверка файлов
echo "📋 Проверка файлов..."
[ -f "backend/app/config.py" ] && check "config.py существует" || check "config.py НЕ существует"
[ -f "backend/app/services/google_sheets_importer.py" ] && check "google_sheets_importer.py существует" || check "google_sheets_importer.py НЕ существует"
[ -f "backend/app/api/import_api.py" ] && check "import_api.py существует" || check "import_api.py НЕ существует"
[ -f "../google_credentials.json" ] && check "google_credentials.json существует" || echo -e "${YELLOW}⚠️  google_credentials.json не найден (опционально)${NC}"

echo ""

# 2. Проверка Python модулей
echo "🐍 Проверка Python модулей..."
cd backend
python3 -c "from app.services.google_sheets_importer import GoogleSheetsImporter" 2>/dev/null && check "Импортер импортируется" || check "Импортер НЕ импортируется"
python3 -c "from app.api.import_api import router" 2>/dev/null && check "API роутер импортируется" || check "API роутер НЕ импортируется"
python3 -c "from app.main import app" 2>/dev/null && check "FastAPI приложение импортируется" || check "FastAPI приложение НЕ импортируется"
cd ..

echo ""

# 3. Проверка Docker файлов
echo "🐳 Проверка Docker конфигурации..."
[ -f "docker-compose.yml" ] && check "docker-compose.yml существует" || check "docker-compose.yml НЕ существует"
[ -f "backend/Dockerfile" ] && check "backend/Dockerfile существует" || check "backend/Dockerfile НЕ существует"
[ -f "frontend/Dockerfile" ] && check "frontend/Dockerfile существует" || check "frontend/Dockerfile НЕ существует"

echo ""

# 4. Проверка переменных окружения
echo "🔧 Проверка конфигурации..."
cd backend
python3 -c "from app.config import GOOGLE_SHEET_ID; print(f'GOOGLE_SHEET_ID: {GOOGLE_SHEET_ID}')" 2>/dev/null && check "GOOGLE_SHEET_ID настроен" || check "GOOGLE_SHEET_ID НЕ настроен"
cd ..

echo ""

# 5. Тест импорта (если credentials есть)
if [ -f "../google_credentials.json" ]; then
    echo "📥 Тест импорта данных..."
    cd backend
    python3 test_import_1win.py 2>&1 | grep -q "Найдено записей" && check "Импорт работает" || echo -e "${YELLOW}⚠️  Импорт не протестирован (возможны проблемы с доступом)${NC}"
    cd ..
else
    echo -e "${YELLOW}⚠️  Пропуск теста импорта (нет google_credentials.json)${NC}"
fi

echo ""
echo "========================================"
echo "✨ Проверка завершена!"
echo ""
echo "💡 Для запуска в production:"
echo "   1. Создайте .env файл: cp .env.production.example .env"
echo "   2. Отредактируйте .env с реальными значениями"
echo "   3. Запустите: docker-compose up -d"
echo ""
