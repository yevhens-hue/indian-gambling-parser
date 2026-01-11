# 🚀 Руководство по деплою в production

## 📋 Реализованные улучшения

### ✅ 1. Real-time обновления через WebSocket
- Backend: WebSocket endpoint `/api/ws/updates`
- Frontend: Автоматическое переподключение и обновление данных
- Мониторинг изменений в БД каждые 5 секунд

### ✅ 2. Авторизация (JWT)
- Endpoints: `/api/auth/login`, `/api/auth/me`
- По умолчанию: username=`admin`, password=`admin123`
- **ВНИМАНИЕ:** Измените пароль в production!

### ✅ 3. Оптимизация производительности
- Server-side пагинация
- React Query кеширование
- Виртуализация таблицы (готово к использованию)

### ✅ 4. Графики и визуализация
- Recharts для графиков статистики
- Барные графики и круговые диаграммы
- Топ провайдеров

### ✅ 5. Docker контейнеризация
- Dockerfile для backend (Python)
- Dockerfile для frontend (multi-stage build)
- docker-compose.yml для оркестрации
- nginx конфигурация для frontend

---

## 🐳 Docker деплой

### Быстрый старт

```bash
cd web_service

# Создайте .env файл (опционально)
cat > .env << EOF
SECRET_KEY=your-very-secret-key-change-me
AUTH_ENABLED=true
EOF

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Отдельная сборка сервисов

**Backend:**
```bash
cd web_service/backend
docker build -t providers-backend .
docker run -p 8000:8000 \
  -v $(pwd)/../../providers_data.db:/app/data/providers_data.db \
  -v $(pwd)/../../storage.py:/app/storage.py \
  providers-backend
```

**Frontend:**
```bash
cd web_service/frontend
docker build -t providers-frontend .
docker run -p 80:80 providers-frontend
```

---

## 🔐 Настройка авторизации

### Включение авторизации

1. Установите переменную окружения:
   ```bash
   export AUTH_ENABLED=true
   export SECRET_KEY="your-very-secret-key-here"
   ```

2. Измените пароль по умолчанию в `backend/app/auth/auth.py`:
   ```python
   USERS_DB = {
       "admin": {
           "username": "admin",
           "hashed_password": get_password_hash("YOUR_STRONG_PASSWORD"),
           "role": "admin"
       }
   }
   ```

3. Или создайте несколько пользователей в БД (рекомендуется для production)

### Использование авторизации

**Login:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Использование токена:**
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🌐 Nginx конфигурация для production

Создайте файл `web_service/nginx/nginx.conf`:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## ⚡ Оптимизация производительности

### Для больших объемов данных (10k+ записей)

1. **Виртуализация таблицы** - уже реализовано в DataGrid
2. **Индексы в БД:**
   ```sql
   CREATE INDEX idx_merchant ON providers(merchant);
   CREATE INDEX idx_provider_domain ON providers(provider_domain);
   CREATE INDEX idx_timestamp ON providers(timestamp_utc);
   ```

3. **Кеширование на уровне API:**
   - Добавьте Redis для кеширования статистики
   - Используйте FastAPI dependency для кеша

4. **Пагинация:**
   - Уже реализована (по умолчанию 50 записей)
   - Можно увеличить `MAX_PAGE_SIZE` в `config.py`

---

## 📊 Мониторинг

### Health checks

```bash
# Backend health
curl http://localhost:8000/health

# Docker health check
docker-compose ps
```

### Логи

```bash
# Все логи
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

---

## 🔧 Переменные окружения

### Backend

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `DB_PATH` | Путь к SQLite БД | `providers_data.db` |
| `SECRET_KEY` | Секретный ключ для JWT | `change-me` |
| `AUTH_ENABLED` | Включить авторизацию | `false` |
| `CORS_ORIGINS` | Разрешенные origins | `localhost:5173` |

### Frontend

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `VITE_API_URL` | URL backend API | `http://localhost:8000/api` |
| `VITE_WS_URL` | URL WebSocket | `ws://localhost:8000/api/ws/updates` |

---

## 🚀 Production чеклист

- [ ] Изменить `SECRET_KEY` на случайную строку
- [ ] Включить `AUTH_ENABLED=true`
- [ ] Изменить пароль по умолчанию
- [ ] Настроить SSL/TLS (HTTPS)
- [ ] Настроить доменное имя
- [ ] Настроить backup БД
- [ ] Настроить мониторинг (Prometheus, Grafana)
- [ ] Настроить логирование (ELK stack или аналог)
- [ ] Настроить rate limiting
- [ ] Проверить безопасность (OWASP Top 10)

---

## 📝 Дополнительные улучшения

### Redis для кеширования

Добавьте в `docker-compose.yml`:
```yaml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

### PostgreSQL вместо SQLite

Для production рекомендуется PostgreSQL:
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: providers
    POSTGRES_USER: user
    POSTGRES_PASSWORD: password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

---

## 🔗 Полезные команды

```bash
# Пересборка после изменений
docker-compose build --no-cache

# Просмотр использования ресурсов
docker stats

# Бэкап БД
docker exec providers-backend sqlite3 /app/data/providers_data.db .dump > backup.sql

# Восстановление БД
cat backup.sql | docker exec -i providers-backend sqlite3 /app/data/providers_data.db
```

---

## 📚 Документация

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx Docs](https://nginx.org/en/docs/)
- [React Query](https://tanstack.com/query/latest)
