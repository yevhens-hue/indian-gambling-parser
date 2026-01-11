# 📊 Providers Dashboard - Web Service

Веб-сервис для управления данными провайдеров платежных систем с реальным временем обновления, аналитикой и импортом данных.

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+
- SQLite (встроенный)
- Redis (опционально, для кэширования)
- Docker (опционально, для production)

### Локальный запуск

#### Backend

```bash
cd web_service/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd web_service/frontend
npm install
npm run dev
```

### Docker

```bash
cd web_service
docker-compose up -d
```

## 📚 Документация

### Основная документация

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - Подробное описание работы сервиса
- [QUICK_OVERVIEW.md](QUICK_OVERVIEW.md) - Краткий обзор архитектуры
- [ARCHITECTURE.md](ARCHITECTURE.md) - Детальная архитектура
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [LOCAL_RUN.md](LOCAL_RUN.md) - Запуск без Docker

### Статус улучшений

- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) - Итоговый отчет
- [FINAL_STATUS_ALL.md](FINAL_STATUS_ALL.md) - Финальный статус
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Полный список улучшений

## 🎯 Основные возможности

### ✅ Реализовано

- 📊 Dashboard с аналитикой и графиками
- 🔄 Real-time обновления через WebSocket
- 🔍 Фильтрация и поиск провайдеров
- 📥 Импорт данных из Google Sheets
- 📤 Экспорт в XLSX, CSV, JSON, PDF
- 🔐 Авторизация и аутентификация
- 📈 Статистика и аналитика
- 🔔 Уведомления (Email/Telegram)
- 📝 Audit Log (история изменений)
- 🔗 Фильтры в URL (sharing)
- ⚡ Оптимизация производительности
- 🔒 Безопасность (Rate Limiting, валидация)
- 📊 Мониторинг (Prometheus, Sentry, Health Checks)
- 🧪 Тестирование (Unit, Integration)
- 🚀 CI/CD (GitHub Actions)

### ⏳ В разработке

- ML прогнозирование
- PostgreSQL миграция
- Горизонтальное масштабирование
- Kubernetes конфигурация

## 🏗️ Архитектура

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
│   Port: 5173    │
└────────┬────────┘
         │ HTTP/WebSocket
         │
┌────────▼────────┐
│   Backend       │
│   (FastAPI)     │
│   Port: 8000    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼───┐
│SQLite │ │Redis │
│  DB   │ │Cache │
└───────┘ └──────┘
```

## 📦 API Endpoints

### Основные

- `GET /api/providers` - Список провайдеров
- `GET /api/providers/{id}` - Провайдер по ID
- `PUT /api/providers/{id}` - Обновить провайдер
- `POST /api/providers/batch-delete` - Массовое удаление
- `PUT /api/providers/batch-update` - Массовое обновление

### Статистика

- `GET /api/providers/stats/statistics` - Общая статистика
- `GET /api/analytics/dashboard` - Dashboard метрики

### Экспорт

- `GET /api/export/xlsx` - Excel (обычный)
- `GET /api/export/xlsx?formatted=true` - Excel (форматированный)
- `GET /api/export/pdf` - PDF отчет
- `GET /api/export/csv` - CSV
- `GET /api/export/json` - JSON

### Импорт

- `POST /api/import/google-sheets` - Импорт из Google Sheets
- `GET /api/import/preview` - Превью данных

### Мониторинг

- `GET /health` - Health Check
- `GET /metrics` - Prometheus метрики

### Audit Log

- `GET /api/audit/log` - История изменений
- `GET /api/audit/log/{record_id}` - История конкретной записи

### WebSocket

- `WS /ws` - Real-time обновления

## 🔧 Конфигурация

### Переменные окружения

#### Backend

```bash
# Database
DB_PATH=providers_data.db

# Redis (опционально)
REDIS_URL=redis://localhost:6379

# Google Sheets (опционально)
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_PATH=path/to/credentials.json

# Sentry (опционально)
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=production

# Email/Telegram (опционально)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password
EMAIL_FROM=your_email@gmail.com
NOTIFICATION_EMAILS=email1@example.com,email2@example.com
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

#### Frontend

```bash
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

## 🧪 Тестирование

### Backend тесты

```bash
cd web_service/backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Frontend тесты

```bash
cd web_service/frontend
npm test
```

## 🚀 Production

### Docker Compose

```bash
cd web_service
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx + SSL

См. [nginx/README.md](nginx/README.md) для настройки HTTPS.

### CI/CD

GitHub Actions настроены автоматически:
- Тесты на каждый push/PR
- Docker builds
- Releases

## 📊 Статистика улучшений

**Завершено: 23/35 улучшений (66%)**

### Критичные категории: 100%
- ✅ Производительность (5/5)
- ✅ Безопасность (3/3)
- ✅ Мониторинг (4/4)
- ✅ Тестирование (2/2)
- ✅ DevOps (2/2)

### Функциональность: 87.5%
- ✅ 7/8 функций реализовано

## 📝 Лицензия

[Укажите лицензию]

## 👥 Авторы

[Укажите авторов]

---

**Дата последнего обновления:** 2026-01-11
