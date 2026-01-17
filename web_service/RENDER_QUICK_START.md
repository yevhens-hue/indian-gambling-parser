# ⚡ Быстрый старт на Render.com

## 🚀 За 5 минут

### Шаг 1: Подготовка Redis

1. Откройте [Render Dashboard](https://dashboard.render.com/)
2. **New +** → **Redis**
3. Настройки:
   - Name: `indian-gambling-parser-redis`
   - Plan: `Free` (для теста) или `Starter`
   - Region: `Frankfurt`
4. **Create Redis** ✅

---

### Шаг 2: Деплой Backend

1. **New +** → **Blueprint**
2. Подключите ваш GitHub репозиторий
3. Render автоматически обнаружит `render.yaml`
4. Проверьте настройки и нажмите **Apply**
5. Дождитесь деплоя (2-5 минут) ✅

**Или вручную:**

1. **New +** → **Web Service**
2. Подключите репозиторий
3. Настройки:
   ```
   Name: indian-gambling-parser-api
   Environment: Docker
   Dockerfile Path: web_service/backend/Dockerfile
   Docker Context: web_service/backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment Variables**:
   ```
   ENVIRONMENT=production
   REDIS_URL=<link to Redis service>
   CORS_ORIGINS=https://your-frontend.onrender.com
   ```
5. **Create Web Service** ✅

---

### Шаг 3: Деплой Frontend

1. **New +** → **Web Service**
2. Подключите репозиторий
3. Настройки:
   ```
   Name: indian-gambling-parser-frontend
   Environment: Docker
   Dockerfile Path: web_service/frontend/Dockerfile
   Docker Context: web_service/frontend
   ```
4. **Environment Variables**:
   ```
   VITE_API_URL=https://indian-gambling-parser-api.onrender.com
   VITE_WS_URL=wss://indian-gambling-parser-api.onrender.com
   ```
5. **Create Web Service** ✅

---

## ✅ Проверка

1. Backend: `https://your-api.onrender.com/health`
2. Frontend: `https://your-frontend.onrender.com`
3. Redis: проверьте логи Backend

---

## 🔗 Связывание сервисов

В настройках Backend:
- **Environment** → **Link Redis** → выберите ваш Redis

---

## 📝 Важно

- URL сервисов: `https://your-service-name.onrender.com`
- Redis URL устанавливается автоматически при связывании
- Автоматический деплой при каждом push в `main`

---

**Готово!** 🎉
