# 🚀 Инструкция по запуску сервисов

Эта инструкция поможет вам запустить все необходимые сервисы для работы приложения.

## 📋 Предварительные требования

1. Python 3.8+
2. Node.js 16+ (для frontend)
3. Redis (опционально, для кэширования)

## 🔧 Backend (FastAPI)

### 1. Установка зависимостей

```bash
cd web_service/backend
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в директории `web_service/backend/`:

```bash
# Database
DB_PATH=../providers_data.db

# Security
ENVIRONMENT=development  # или production
JWT_SECRET_KEY=your-secret-key-here
AUTH_ENABLED=false

# IP Filter (опционально)
IP_FILTER_ENABLED=false
IP_WHITELIST=127.0.0.1
IP_BLACKLIST=

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Google Sheets (опционально)
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_PATH=../google_credentials.json
```

### 3. Запуск backend сервера

```bash
# Из директории web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Или используйте скрипт:

```bash
python -m app.main
```

Backend будет доступен по адресу: `http://localhost:8000`

### 4. Проверка работы backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## 🎨 Frontend (React/Vite)

### 1. Установка зависимостей

```bash
cd web_service/frontend
npm install
```

### 2. Настройка переменных окружения

Создайте файл `.env` в директории `web_service/frontend/`:

```bash
VITE_API_URL=http://localhost:8000
```

### 3. Запуск frontend сервера

```bash
npm run dev
```

Frontend будет доступен по адресу: `http://localhost:5173`

---

## 🐳 Docker Compose (альтернативный способ)

Если у вас установлен Docker, можно использовать docker-compose:

```bash
cd web_service
docker-compose up -d
```

Это запустит:
- Backend на порту 8000
- Frontend на порту 5173
- Redis на порту 6379 (если настроен)

---

## 🔍 Проверка статуса сервисов

### Проверка backend

```bash
# Health check
curl http://localhost:8000/health

# Статус мониторинга
curl http://localhost:8000/api/monitoring/status

# Метрики
curl http://localhost:8000/metrics
```

### Проверка frontend

Откройте в браузере: `http://localhost:5173`

---

## ⚠️ Решение проблем

### Ошибка ERR_CONNECTION_REFUSED

Эта ошибка означает, что сервер не запущен. Проверьте:

1. **Backend не запущен:**
   ```bash
   # Проверьте, запущен ли процесс на порту 8000
   lsof -i :8000
   
   # Если процесс не найден, запустите backend
   cd web_service/backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend не запущен:**
   ```bash
   # Проверьте, запущен ли процесс на порту 5173
   lsof -i :5173
   
   # Если процесс не найден, запустите frontend
   cd web_service/frontend
   npm run dev
   ```

3. **Неправильный URL:**
   - Убедитесь, что frontend использует правильный URL backend в `.env`
   - Проверьте, что порты не заняты другими приложениями

### Порт уже занят

Если порт занят, вы можете:

1. **Изменить порт backend:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **Изменить порт frontend:**
   ```bash
   # В package.json или через переменную окружения
   PORT=5174 npm run dev
   ```

### Проблемы с зависимостями

```bash
# Backend
cd web_service/backend
pip install --upgrade -r requirements.txt

# Frontend
cd web_service/frontend
npm install
```

---

## 📝 Быстрый старт

```bash
# Терминал 1: Backend
cd web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2: Frontend
cd web_service/frontend
npm run dev
```

После запуска:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## ✅ Проверка качества

После запуска сервисов, проверьте качество кода:

```bash
cd web_service/backend
python check_quality.py
```

Этот скрипт проверит:
- Импорты модулей
- Линтинг кода
- Типы
- Тесты
- Порядок middleware
- Security headers
- Переменные окружения
