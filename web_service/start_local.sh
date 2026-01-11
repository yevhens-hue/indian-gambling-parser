#!/bin/bash
# Скрипт для локального запуска без Docker

set -e

echo "🚀 Локальный запуск (без Docker)"
echo "=================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Проверка Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"
echo "✅ Node.js: $(node --version)"
echo ""

# Запуск Backend в фоне
echo "🔧 Запуск Backend..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo "✅ Backend запущен (PID: $BACKEND_PID)"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Ожидание запуска backend
sleep 3

# Запуск Frontend
echo "🌐 Запуск Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend запущен (PID: $FRONTEND_PID)"
echo "   Frontend: http://localhost:5173"
echo ""

echo "=================================="
echo "✅ Сервисы запущены!"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Для остановки выполните:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Или нажмите Ctrl+C"

# Ожидание сигнала
wait
