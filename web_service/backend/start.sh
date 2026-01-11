#!/bin/bash
# Скрипт запуска FastAPI backend для macOS/Linux

PORT=8000

echo "============================================================"
echo "🚀 Запуск FastAPI Backend"
echo "============================================================"

# Проверяем, занят ли порт
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  Порт $PORT уже занят!"
    PID=$(lsof -ti:$PORT | head -1)
    echo "📌 Найден процесс: $PID"
    echo ""
    read -p "Остановить процесс и запустить сервер? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Останавливаю процесс $PID..."
        kill -9 $PID 2>/dev/null
        sleep 1
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo "❌ Не удалось остановить процесс. Используйте: ./stop.sh"
            exit 1
        fi
        echo "✅ Процесс остановлен"
    else
        echo "❌ Отменено. Используйте другой порт или остановите процесс вручную:"
        echo "   ./stop.sh"
        exit 1
    fi
fi

# Определяем путь к python3
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Ошибка: Python не найден. Установите Python 3.8+"
    exit 1
fi

echo "📦 Используется: $PYTHON_CMD"
echo "📁 Директория: $(pwd)"
echo "🌐 Server: http://localhost:$PORT"
echo "📚 API Docs: http://localhost:$PORT/docs"
echo "============================================================"
echo ""

# Запускаем backend
$PYTHON_CMD start.py
