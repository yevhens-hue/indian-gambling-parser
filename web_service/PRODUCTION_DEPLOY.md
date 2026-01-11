# 🚀 Production Deployment Guide

## ✅ Подготовка к продакшн деплою

### 1. Настройка переменных окружения

Создайте файл `.env` в директории `web_service/`:

```bash
cd web_service
cp .env.production.example .env
```

Отредактируйте `.env` и укажите реальные значения:

```bash
# Обязательно измените!
SECRET_KEY=your-very-secret-key-minimum-32-characters-long
AUTH_ENABLED=true

# Google Sheets (если используете импорт)
GOOGLE_SHEET_ID=1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
```

### 2. Подготовка файлов

Убедитесь, что существуют следующие файлы:

```bash
# В корне проекта
google_credentials.json          # Service Account ключ для Google Sheets
providers_data.db                # БД (создастся автоматически если нет)
screenshots/                     # Директория для скриншотов
```

### 3. Проверка Google Sheets API

Если используете импорт данных из Google Sheets:

1. **Файл credentials:**
   ```bash
   ls google_credentials.json
   ```

2. **Права доступа:**
   - Откройте Google Таблицу
   - Добавьте email из `google_credentials.json` (поле `client_email`) как редактор

3. **Тест подключения:**
   ```bash
   cd web_service/backend
   python3 test_import_1win.py
   ```

---

## 🐳 Docker Production Deployment

### Шаг 1: Сборка образов

```bash
cd web_service

# Сборка всех сервисов
docker-compose build

# Или отдельно:
docker-compose build backend
docker-compose build frontend
```

### Шаг 2: Запуск сервисов

```bash
# Запуск в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps
```

### Шаг 3: Проверка работоспособности

```bash
# Health check backend
curl http://localhost:8000/health

# Проверка frontend
curl http://localhost:80

# Проверка API
curl http://localhost:8000/api/providers?limit=1
```

---

## 🔐 Настройка безопасности

### 1. Изменение пароля по умолчанию

В production **ОБЯЗАТЕЛЬНО** измените пароль администратора:

```python
# backend/app/auth/auth.py
from app.auth.auth import get_password_hash

USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("YOUR_STRONG_PASSWORD_HERE"),
        "role": "admin"
    }
}
```

Или используйте переменные окружения (рекомендуется):

```bash
# Создайте файл с паролем
export ADMIN_PASSWORD=$(openssl rand -base64 32)

# Используйте его в контейнере
docker-compose.yml:
  environment:
    - ADMIN_PASSWORD=${ADMIN_PASSWORD}
```

### 2. Настройка CORS

Отредактируйте `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

### 3. Использование HTTPS

В production используйте reverse proxy (nginx/traefik) с SSL сертификатами.

---

## 📊 Мониторинг и логирование

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend

# Последние 100 строк
docker-compose logs --tail=100 backend
```

### Health checks

Все сервисы имеют встроенные health checks:

- **Backend:** `http://localhost:8000/health`
- **Frontend:** Проверка доступности на порту 80

---

## 🔄 Обновление приложения

### 1. Обновление кода

```bash
# Получить обновления
git pull

# Пересобрать образы
docker-compose build

# Перезапустить сервисы
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

### 2. Обновление данных

Данные хранятся в volume, поэтому при обновлении они сохраняются:

```yaml
volumes:
  - ../providers_data.db:/app/data/providers_data.db
```

---

## 🧪 Тестирование в production-режиме

### 1. Локальное тестирование

```bash
# Запуск с production переменными
cd web_service
docker-compose up -d

# Тест импорта
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"

# Проверка данных
curl "http://localhost:8000/api/providers?merchant=1win&limit=5"
```

### 2. Тестирование API

```bash
# Скрипт автоматического тестирования
cd web_service/backend
python3 test_api_import.py
```

### 3. Тестирование через веб-интерфейс

1. Откройте http://localhost:80 (или ваш домен)
2. Проверьте импорт данных
3. Проверьте фильтры и статистику
4. Проверьте экспорт данных

---

## 🌐 Деплой на сервер

### Вариант 1: Docker на сервере

```bash
# На сервере
git clone <your-repo>
cd indian_gambling_parser/web_service

# Создайте .env файл
cp .env.production.example .env
nano .env  # Отредактируйте значения

# Запуск
docker-compose up -d
```

### Вариант 2: С nginx reverse proxy

```nginx
# /etc/nginx/sites-available/providers
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📝 Чеклист перед продакшн

- [ ] Изменен `SECRET_KEY` на случайный длинный ключ
- [ ] Изменен пароль администратора
- [ ] `AUTH_ENABLED=true` (если нужна авторизация)
- [ ] Настроены правильные CORS origins
- [ ] Google Sheets credentials настроены (если используется импорт)
- [ ] БД и screenshots директории имеют правильные права
- [ ] Логирование настроено и проверено
- [ ] Health checks работают
- [ ] Backup БД настроен
- [ ] HTTPS настроен (через nginx/traefik)
- [ ] Мониторинг настроен (опционально)

---

## 🆘 Troubleshooting

### Проблема: Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend

# Проверьте переменные окружения
docker-compose config

# Проверьте порты
netstat -tulpn | grep 8000
```

### Проблема: Импорт не работает

```bash
# Проверьте credentials
ls -la google_credentials.json

# Проверьте доступ к Google Sheets
python3 test_import_1win.py

# Проверьте переменные окружения
docker-compose exec backend env | grep GOOGLE
```

### Проблема: Frontend не подключается к API

```bash
# Проверьте VITE_API_URL в .env
cat web_service/frontend/.env

# Проверьте nginx конфигурацию
docker-compose exec frontend cat /etc/nginx/nginx.conf
```

---

## 📚 Дополнительные ресурсы

- **DEPLOYMENT.md** - Общее руководство по деплою
- **IMPORT_1WIN.md** - Инструкция по импорту данных
- **TROUBLESHOOTING.md** - Решение проблем
- **COMPLETE_FEATURES_GUIDE.md** - Описание всех функций

---

**Готово к production деплою! 🚀**
