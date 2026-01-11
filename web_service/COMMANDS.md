# 🚀 Команды запуска

## 📋 Быстрый старт

### Вариант 1: Автоматический запуск (рекомендуется)

```bash
cd web_service
./start_local.sh
```

Этот скрипт запустит backend и опционально frontend.

---

### Вариант 2: Ручной запуск

#### Terminal 1: Backend

```bash
cd web_service/backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или: venv\Scripts\activate  # Windows
pip install -r requirements.txt
python3 start.py
```

**Backend будет доступен:** http://localhost:8000

#### Terminal 2: Frontend

```bash
cd web_service/frontend
npm install  # только первый раз
npm run dev
```

**Frontend будет доступен:** http://localhost:5173

---

## 🔧 Полезные команды

### Остановка процессов

```bash
# Найти процесс на порту 8000
lsof -ti:8000

# Остановить процесс
lsof -ti:8000 | xargs kill -9

# Или использовать скрипт
cd web_service/backend
./stop.sh
```

### Проверка работоспособности

```bash
# Health check backend
curl http://localhost:8000/health

# Проверка API
curl http://localhost:8000/api/providers?limit=1

# API документация
open http://localhost:8000/docs
```

---

## 📥 Импорт данных

### Импорт из Google Sheets

```bash
# Предпросмотр (первые 10 записей)
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=10"

# Импорт всех данных
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Через веб-интерфейс

1. Откройте http://localhost:5173
2. Найдите блок "Импорт данных из Google Sheets"
3. Нажмите "Импортировать"

---

## 🐳 Docker запуск (если установлен)

### Быстрый запуск

```bash
cd web_service

# Создать .env файл (если еще нет)
cp .env.example .env
nano .env  # Отредактировать SECRET_KEY

# Запуск
docker compose up -d

# Логи
docker compose logs -f

# Остановка
docker compose down
```

### Отдельная сборка

```bash
# Backend
cd web_service/backend
docker build -t providers-backend .
docker run -p 8000:8000 providers-backend

# Frontend
cd web_service/frontend
docker build -t providers-frontend .
docker run -p 80:80 providers-frontend
```

---

## 🧪 Тестирование

### Тест импорта данных

```bash
cd web_service/backend
python3 test_import_1win.py
```

### Тест API

```bash
cd web_service/backend
python3 test_api_import.py
```

### Тест конфигурации

```bash
cd web_service
./test_production.sh
```

---

## 📊 Проверка данных

### Проверка провайдеров в БД

```bash
# Все провайдеры
curl "http://localhost:8000/api/providers?limit=10"

# Только 1win
curl "http://localhost:8000/api/providers?merchant=1win&limit=10"

# Статистика
curl "http://localhost:8000/api/providers/stats/statistics"
```

### Экспорт данных

```bash
# XLSX
curl "http://localhost:8000/api/export/xlsx" -o providers.xlsx

# CSV
curl "http://localhost:8000/api/export/csv" -o providers.csv

# JSON
curl "http://localhost:8000/api/export/json" -o providers.json
```

---

## 🔍 Логи и отладка

### Просмотр логов backend

```bash
# Если запущен через start.py - логи в консоли
# Если через Docker:
docker compose logs -f backend

# Или напрямую:
cd web_service/backend
python3 start.py  # логи в терминале
```

### Просмотр логов frontend

```bash
# Логи в терминале где запущен npm run dev
# Или через Docker:
docker compose logs -f frontend
```

### Проверка WebSocket

```bash
# В консоли браузера (F12) должно быть:
# ✅ WebSocket подключен
```

---

## ⚙️ Настройка

### Переменные окружения (Backend)

```bash
# Создать .env файл в web_service/backend/
cat > web_service/backend/.env << EOF
SECRET_KEY=your-secret-key
AUTH_ENABLED=false
DB_PATH=../../providers_data.db
GOOGLE_SHEET_ID=1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
GOOGLE_CREDENTIALS_PATH=../../google_credentials.json
EOF
```

### Переменные окружения (Frontend)

```bash
# Создать .env файл в web_service/frontend/
cat > web_service/frontend/.env << EOF
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws/updates
EOF
```

---

## 🛠️ Установка зависимостей

### Backend

```bash
cd web_service/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd web_service/frontend
npm install
```

---

## 📝 Часто используемые команды

```bash
# Перезапуск backend
cd web_service/backend
./stop.sh && python3 start.py

# Перезапуск frontend (в другом терминале)
cd web_service/frontend
npm run dev

# Проверка портов
lsof -ti:8000  # Backend
lsof -ti:5173  # Frontend dev
lsof -ti:80    # Frontend production

# Очистка кеша frontend
cd web_service/frontend
rm -rf node_modules/.vite
npm run dev
```

---

## 🔄 Обновление кода

```bash
# Backend - перезапуск
cd web_service/backend
# Остановить (Ctrl+C или ./stop.sh)
python3 start.py

# Frontend - автоматическая перезагрузка при изменениях
# Если не работает:
cd web_service/frontend
npm run dev -- --force
```

---

## 📚 Документация

- **LOCAL_RUN.md** - Подробная инструкция локального запуска
- **PRODUCTION_DEPLOY.md** - Production деплой
- **IMPORT_1WIN.md** - Импорт данных
- **WEBSOCKET_TROUBLESHOOTING.md** - Решение проблем WebSocket

---

**Все команды готовы к использованию! 🚀**
