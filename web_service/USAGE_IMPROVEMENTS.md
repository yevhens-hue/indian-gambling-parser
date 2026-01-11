# 📖 Как использовать улучшения

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd web_service/backend
pip install -r requirements.txt
```

**Новые зависимости:**
- `slowapi` - Rate limiting
- `prometheus-client` - Метрики
- `redis` (опционально) - Кэширование
- `pytest` - Тестирование

---

## 2. Запуск сервиса

### Development режим:

```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=console
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Результат:**
- ✅ Цветные логи в консоли
- ✅ Подробное логирование (DEBUG уровень)
- ✅ Автоперезагрузка при изменениях

### Production режим:

```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
export LOG_FILE=/var/log/providers-api.log
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Результат:**
- ✅ JSON логи (удобно для парсинга)
- ✅ Логи в файл
- ✅ Оптимальная производительность

---

## 3. Проверка работы

### Health Check:
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Prometheus метрики:
```bash
curl http://localhost:8000/metrics
# Метрики в формате Prometheus
```

### Rate Limiting:
```bash
# Должно вернуть 200
curl http://localhost:8000/api/providers?limit=10

# После 200 запросов - 429
for i in {1..250}; do curl -s http://localhost:8000/api/providers > /dev/null; done
```

---

## 4. Redis кэширование (опционально)

### Установка Redis:

**macOS:**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Настройка:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
# или
export REDIS_URL=redis://localhost:6379/0
```

**Проверка:**
- Если Redis доступен → кэширование работает
- Если Redis недоступен → работает без кэша (fallback)

### Очистка кэша:

```bash
# Очистить все
curl -X POST http://localhost:8000/api/providers/cache/clear

# Очистить по паттерну
curl -X POST "http://localhost:8000/api/providers/cache/clear?pattern=statistics:*"
```

---

## 5. Prometheus мониторинг

### Настройка Prometheus:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'providers-api'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          instance: 'providers-api-dev'
```

### Доступные метрики:

```
# HTTP метрики
http_requests_total{method="GET",endpoint="/api/providers",status_code="200"}
http_request_duration_seconds{method="GET",endpoint="/api/providers"}

# Бизнес метрики
providers_total
providers_by_merchant{merchant="1win"}

# Кэш метрики
cache_hits_total{cache_key_prefix="statistics"}
cache_misses_total{cache_key_prefix="statistics"}

# БД метрики
db_query_duration_seconds{query_type="get_all_providers"}

# WebSocket метрики
websocket_connections_active
```

### Grafana Dashboard:

Импортируйте метрики в Grafana для визуализации:
- HTTP requests rate
- Request duration
- Cache hit rate
- Providers count
- WebSocket connections

---

## 6. Тестирование

### Запуск всех тестов:

```bash
pytest tests/ -v
```

### С покрытием кода:

```bash
pytest tests/ --cov=storage --cov=app --cov-report=html
open htmlcov/index.html  # macOS
```

### Конкретный тест:

```bash
pytest tests/test_storage.py::test_save_provider -v
```

---

## 7. Логирование

### Просмотр логов:

**Development (консоль):**
```bash
# Логи выводятся в консоль с цветами
```

**Production (файл):**
```bash
tail -f /var/log/providers-api.log | jq '.'  # JSON формат
```

### Фильтрация логов:

```bash
# Только ошибки
grep '"level":"ERROR"' logs/api.log

# Запросы к конкретному endpoint
grep '"path":"/api/providers"' logs/api.log

# Запросы медленнее 1 секунды
jq 'select(.process_time_ms > 1000)' logs/api.log
```

---

## 8. Мониторинг производительности

### Проверка индексов БД:

```bash
sqlite3 providers_data.db
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='providers';
.exit
```

### Проверка метрик:

```bash
# Все метрики
curl http://localhost:8000/metrics

# Конкретная метрика (Prometheus query)
curl 'http://localhost:8000/metrics' | grep http_requests_total
```

### Анализ логов:

```bash
# Время обработки запросов
jq -r 'select(.message=="Request completed") | "\(.path): \(.process_time_ms)ms"' logs/api.log

# Топ медленных запросов
jq -r 'select(.message=="Request completed") | "\(.process_time_ms) \(.path)"' logs/api.log | sort -rn | head -10
```

---

## 9. Troubleshooting

### Проблема: Redis недоступен

**Решение:** Это нормально. Кэширование просто не работает, но все остальное работает.

**Проверка:**
```bash
redis-cli ping
# Должно вернуть: PONG
```

### Проблема: Метрики не работают

**Решение:** Убедитесь что prometheus-client установлен:
```bash
pip install prometheus-client
```

### Проблема: Rate limiting слишком строгий

**Решение:** Измените в `app/main.py`:
```python
limiter = Limiter(key_func=get_remote_address, default_limits=["500/minute"])
```

### Проблема: Логи не сохраняются

**Решение:** Проверьте права на запись:
```bash
touch logs/api.log
chmod 666 logs/api.log
```

---

## 10. Production Checklist

- [ ] ✅ Установлены все зависимости
- [ ] ✅ Настроено логирование (JSON формат)
- [ ] ✅ Настроен Redis (опционально)
- [ ] ✅ Настроен Prometheus (опционально)
- [ ] ✅ Rate limiting настроен правильно
- [ ] ✅ Тесты проходят (`pytest tests/ -v`)
- [ ] ✅ Health check работает (`/health`)
- [ ] ✅ Metrics endpoint работает (`/metrics`)
- [ ] ✅ Логи пишутся в файл
- [ ] ✅ Environment variables настроены

---

## 📚 Полезные команды

```bash
# Запуск сервера
uvicorn app.main:app --reload

# Тесты
pytest tests/ -v

# Проверка метрик
curl http://localhost:8000/metrics

# Очистка кэша
curl -X POST http://localhost:8000/api/providers/cache/clear

# Проверка Redis
redis-cli ping

# Просмотр логов
tail -f logs/api.log | jq '.'

# Проверка индексов БД
sqlite3 providers_data.db ".indexes providers"
```

---

**Все готово к использованию!** ✅
