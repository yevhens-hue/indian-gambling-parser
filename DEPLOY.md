# 🚀 Деплой проекта

## Быстрый деплой на Render.com (бесплатно)

### Шаг 1: Подготовка
```bash
# Убедитесь, что код в GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### Шаг 2: Деплой на Render

1. Зайдите на [render.com](https://render.com) и войдите через GitHub

2. Нажмите **New** → **Blueprint**

3. Подключите ваш репозиторий `indian_gambling_parser`

4. Render автоматически найдёт `render.yaml` и создаст:
   - ✅ Redis (кэширование)
   - ✅ Backend API (Python/FastAPI)
   - ✅ Frontend (React)

5. Нажмите **Apply** и дождитесь деплоя (~5-10 минут)

### Шаг 3: Получите ссылки

После деплоя вы получите:
- **Frontend**: `https://providers-frontend.onrender.com`
- **API**: `https://providers-api.onrender.com`
- **API Docs**: `https://providers-api.onrender.com/docs`

---

## Настройка переменных окружения

В Render Dashboard можете добавить:

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `JWT_SECRET_KEY` | Секретный ключ (генерируется автоматически) | ✅ |
| `GOOGLE_SHEET_ID` | ID Google таблицы для импорта | ❌ |
| `ADMIN_PASSWORD` | Пароль админа (по умолчанию: admin123) | ❌ |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота для уведомлений | ❌ |
| `TELEGRAM_CHAT_ID` | Chat ID для уведомлений | ❌ |

---

## После деплоя

### Проверить работу:
```bash
# Проверить API
curl https://providers-api.onrender.com/health

# Посмотреть провайдеров
curl https://providers-api.onrender.com/api/providers
```

### Импортировать данные:
1. Откройте `https://providers-api.onrender.com/docs`
2. Используйте endpoint `/api/import/google-sheets`

---

## Масштабирование

Когда проект вырастет, можно:

1. **Перейти на платный план Render** — больше ресурсов, без cold starts
2. **Использовать VPS** (DigitalOcean, Hetzner) — полный контроль
3. **Kubernetes** — для enterprise

---

## Локальная разработка

Для тестирования локально:
```bash
cd web_service
./start_local.sh
```

Или через Docker:
```bash
cd web_service
docker-compose up
```
