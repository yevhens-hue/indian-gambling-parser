#!/bin/bash
# Скрипт для остановки backend сервера

PORT=8000

echo "🔍 Поиск процесса на порту $PORT..."

PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
    echo "✅ Порт $PORT свободен. Никаких процессов не найдено."
    exit 0
fi

echo "📌 Найден процесс: $PID"
echo "🛑 Останавливаю процесс..."

kill $PID

sleep 1

# Проверяем, что процесс остановлен
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  Процесс не остановился, пробую force kill..."
    kill -9 $PID
    sleep 1
fi

if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "❌ Не удалось остановить процесс"
    exit 1
else
    echo "✅ Процесс успешно остановлен. Порт $PORT свободен."
fi
