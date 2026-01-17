# 🚀 Деплой на Render.com

**Дата:** 2026-01-11  
**Платформа:** Render.com

---

## 📋 Подготовка

### 1. Требования

- GitHub репозиторий с кодом
- Render.com аккаунт
- Redis (можно использовать Render Redis)

---

## 🔧 Настройка на Render.com

### Шаг 1: Создание Redis сервиса

1. Перейдите в [Render Dashboard](https://dashboard.render.com/)
2. Нажмите **"New +"** → **"Redis"**
3. Настройки:
   - **Name**: `indian-gambling-parser-redis`
   - **Plan**: Free (для начала)
   - **Region**: Выберите ближайший
4. Нажмите **"Create Redis"**
5. Скопируйте **Internal Redis URL** (будет использоваться в backend)

---

### Шаг 2: Создание Backend сервиса

1. Нажмите **"New +"** → **"Web Service"**
2. Подключите GitHub репозиторий
3. Настройки:
   - **Name**: `indian-gambling-parser-backend`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     cd web_service/backend && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd web_service/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Root Directory**: `web_service/backend`

4. **Environment Variables**:
   ```
   REDIS_URL=redis://<your-redis-internal-url>
   REDIS_HOST=<redis-host>
   REDIS_PORT=6379
   REDIS_DB=0
   CACHE_TTL=300
   ENVIRONMENT=production
   DB_PATH=/opt/render/project/src/web_service/backend/data/providers_data.db
   XLSX_PATH=/opt/render/project/src/web_service/backend/data/providers_data.xlsx
   ```

5. Нажмите **"Create Web Service"**

---

### Шаг 3: Создание Frontend сервиса

1. Нажмите **"New +"** → **"Static Site"**
2. Подключите GitHub репозиторий
3. Настройки:
   - **Name**: `indian-gambling-parser-frontend`
   - **Build Command**:
     ```bash
     cd web_service/frontend && npm ci && npm run build
     ```
   - **Publish Directory**: `web_service/frontend/dist`

4. **Environment Variables**:
   ```
   VITE_API_URL=https://indian-gambling-parser-backend.onrender.com
   ```

5. Нажмите **"Create Static Site"**

---

## 🔐 Environment Variables для Backend

```bash
# Redis
REDIS_URL=redis://<internal-redis-url>
REDIS_HOST=<redis-host>
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=300

# Database
DB_PATH=/opt/render/project/src/web_service/backend/data/providers_data.db
XLSX_PATH=/opt/render/project/src/web_service/backend/data/providers_data.xlsx

# Environment
ENVIRONMENT=production

# CORS (замените на ваш frontend URL)
CORS_ORIGINS=https://indian-gambling-parser-frontend.onrender.com

# Optional: Sentry
SENTRY_DSN=<your-sentry-dsn>

# Optional: Notifications
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_USER=<email>
EMAIL_PASSWORD=<password>
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
```

---

## 📝 Render.yaml (опционально)

Создайте `render.yaml` в корне проекта:

```yaml
services:
  - type: redis
    name: indian-gambling-parser-redis
    plan: free
    ipAllowList: []

  - type: web
    name: indian-gambling-parser-backend
    env: python
    buildCommand: cd web_service/backend && pip install -r requirements.txt
    startCommand: cd web_service/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    rootDir: web_service/backend
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: indian-gambling-parser-redis
          property: connectionString
      - key: ENVIRONMENT
        value: production
      - key: CACHE_TTL
        value: 300

  - type: web
    name: indian-gambling-parser-frontend
    env: static
    buildCommand: cd web_service/frontend && npm ci && npm run build
    staticPublishPath: web_service/frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://indian-gambling-parser-backend.onrender.com
```

---

## 🚀 Деплой

1. **Автоматический деплой**: При каждом push в `main` ветку
2. **Ручной деплой**: Нажмите **"Manual Deploy"** → **"Deploy latest commit"**

---

## ✅ Проверка

После деплоя проверьте:

1. **Backend Health**: `https://indian-gambling-parser-backend.onrender.com/health`
2. **API Docs**: `https://indian-gambling-parser-backend.onrender.com/docs`
3. **Frontend**: `https://indian-gambling-parser-frontend.onrender.com`

---

## 🔧 Troubleshooting

### Redis не подключается

- Проверьте `REDIS_URL` в environment variables
- Убедитесь, что Redis сервис запущен
- Проверьте логи backend сервиса

### Backend не запускается

- Проверьте логи в Render Dashboard
- Убедитесь, что все зависимости установлены
- Проверьте `requirements.txt`

### Frontend не подключается к Backend

- Проверьте `VITE_API_URL` в environment variables
- Убедитесь, что CORS настроен правильно
- Проверьте URL backend сервиса

---

## 📚 Дополнительные ресурсы

- [Render Documentation](https://render.com/docs)
- [Render Redis](https://render.com/docs/redis)
- [Render Environment Variables](https://render.com/docs/environment-variables)

---

**Дата:** 2026-01-11  
**Статус:** ✅ Готово к деплою
