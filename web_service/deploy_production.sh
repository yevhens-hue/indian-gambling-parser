#!/bin/bash
# Скрипт для деплоя в production

set -e

echo "🚀 Production Deployment Script"
echo "================================"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker перед продолжением."
    exit 1
fi

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаю из примера..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Файл .env создан из примера"
        echo "💡 Используются настройки по умолчанию (можно отредактировать позже: nano .env)"
    else
        echo "⚠️  Файл .env.example не найден. Используются значения по умолчанию."
        echo "💡 Для production рекомендуется создать .env файл вручную"
    fi
fi

# Проверка google_credentials.json
if [ ! -f "../google_credentials.json" ]; then
    echo "⚠️  Файл google_credentials.json не найден в корне проекта."
    echo "   Импорт из Google Sheets не будет работать."
    read -p "   Продолжить без импорта? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Сборка Docker образов..."
docker compose build

echo ""
echo "🔍 Проверка конфигурации..."
docker compose config > /dev/null && echo "✅ Конфигурация валидна" || {
    echo "❌ Ошибка в конфигурации docker-compose.yml"
    exit 1
}

echo ""
echo "🚀 Запуск сервисов..."
docker compose up -d

echo ""
echo "⏳ Ожидание запуска сервисов (10 секунд)..."
sleep 10

echo ""
echo "🔍 Проверка работоспособности..."

# Проверка backend
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend работает (http://localhost:8000)"
else
    echo "❌ Backend не отвечает"
    echo "   Проверьте логи: docker compose logs backend"
    exit 1
fi

# Проверка frontend
if curl -f -s http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Frontend работает (http://localhost:80)"
else
    echo "⚠️  Frontend может быть еще не запущен. Проверьте: docker compose logs frontend"
fi

echo ""
echo "================================"
echo "✨ Deployment завершен!"
echo ""
echo "📍 Доступные endpoints:"
echo "   - Frontend: http://localhost:80"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Полезные команды:"
echo "   - Логи: docker compose logs -f"
echo "   - Остановка: docker compose down"
echo "   - Перезапуск: docker compose restart"
echo ""
echo "🧪 Тест импорта данных:"
echo "   curl -X POST 'http://localhost:8000/api/import/google-sheets?gid=396039446'"
echo ""
