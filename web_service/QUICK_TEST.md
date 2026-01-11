# ⚡ Быстрый тест Production

## 🧪 Тестирование перед деплоем

### 1. Автоматический тест конфигурации

```bash
cd web_service
./test_production.sh
```

Этот скрипт проверит:
- ✅ Все файлы на месте
- ✅ Python модули импортируются
- ✅ Docker конфигурация валидна
- ✅ Импорт данных работает

---

### 2. Тест импорта данных

```bash
# Проверка парсинга данных
cd web_service/backend
python3 test_import_1win.py

# Результат должен показать:
# ✅ Найдено записей: 335
# ✅ Примеры данных
```

---

### 3. Тест API (если backend запущен)

```bash
# Health check
curl http://localhost:8000/health

# Предпросмотр данных
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"

# Импорт данных (если нужно)
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

---

### 4. Проверка Docker конфигурации

```bash
cd web_service

# Проверка синтаксиса
docker compose config

# Тестовая сборка (без запуска)
docker compose build --no-cache
```

---

### 5. Локальный запуск для теста

```bash
cd web_service

# Запуск в фоне
docker compose up -d

# Проверка статуса
docker compose ps

# Логи
docker compose logs -f

# Остановка
docker compose down
```

---

## ✅ Чеклист перед production

- [ ] Все тесты пройдены (`./test_production.sh`)
- [ ] Импорт данных работает (`test_import_1win.py`)
- [ ] Docker конфигурация валидна (`docker compose config`)
- [ ] .env файл создан и заполнен
- [ ] SECRET_KEY изменен на случайный
- [ ] Пароль администратора изменен (если AUTH_ENABLED=true)
- [ ] google_credentials.json настроен
- [ ] БД и screenshots директории созданы

---

## 🚀 Быстрый деплой

```bash
cd web_service

# Автоматический деплой
./deploy_production.sh
```

Или вручную:

```bash
# 1. Создать .env
cp .env.example .env
nano .env  # Отредактировать

# 2. Сборка и запуск
docker compose build
docker compose up -d

# 3. Проверка
curl http://localhost:8000/health
```

---

**Готово! Все готово к production деплою! 🎉**
