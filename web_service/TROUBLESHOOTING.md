# 🔧 Устранение проблем

## Белая/пустая страница на localhost:5173

### Шаг 1: Проверьте консоль браузера
Откройте DevTools (F12 или Cmd+Option+I на Mac) и проверьте вкладку Console на наличие ошибок.

### Шаг 2: Проверьте Network tab
В DevTools → Network проверьте:
- Есть ли запросы к `/api/providers`?
- Какой статус у запросов (200, 404, 500)?
- Есть ли ошибки CORS?

### Шаг 3: Проверьте, что backend запущен
```bash
curl http://localhost:8000/health
# Должен вернуть: {"status":"ok"}
```

### Шаг 4: Перезапустите frontend
Если вы внесли изменения в код или добавили файл .env:

1. Остановите frontend (Ctrl+C в терминале)
2. Перезапустите:
   ```bash
   cd web_service/frontend
   npm run dev
   ```

### Шаг 5: Очистите кеш браузера
- Hard refresh: Cmd+Shift+R (Mac) или Ctrl+Shift+R (Windows/Linux)
- Или откройте в режиме инкогнито

## Ошибки в консоли браузера

### "Failed to fetch" или "Network Error"
**Причина:** Frontend не может подключиться к backend

**Решение:**
1. Убедитесь, что backend запущен: `curl http://localhost:8000/health`
2. Проверьте файл `.env` в `web_service/frontend/`:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```
3. Перезапустите frontend после изменения .env

### "CORS error" или "Access-Control-Allow-Origin"
**Причина:** Backend не разрешает запросы с frontend

**Решение:**
1. Проверьте файл `web_service/backend/app/main.py`
2. Убедитесь, что в `CORS_ORIGINS` есть `http://localhost:5173`
3. Перезапустите backend

### "Cannot find module" ошибки
**Причина:** Не установлены зависимости или проблемы с импортами

**Решение:**
```bash
cd web_service/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Проблемы с данными

### Таблица пустая, но backend отвечает
**Причина:** Нет данных в БД или ошибка в запросе

**Решение:**
1. Проверьте данные напрямую:
   ```bash
   curl 'http://localhost:8000/api/providers?limit=5'
   ```
2. Если данных нет, запустите парсер:
   ```bash
   python3 main_parser_playwright.py --show-results
   ```

### Данные не обновляются
**Причина:** Кеш React Query

**Решение:**
- Обновите страницу (F5)
- Или очистите кеш в DevTools → Application → Clear storage

## Проблемы с портами

### "Address already in use" на порту 8000
**Решение:**
```bash
cd web_service/backend
./stop.sh
./start.sh
```

### "Address already in use" на порту 5173
**Решение:**
```bash
lsof -ti:5173 | xargs kill -9
```

Или измените порт в `vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 5174
  }
})
```

## Проблемы с зависимостями

### Ошибки импорта модулей
```bash
cd web_service/backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### Python версия
Убедитесь, что используется Python 3.8+:
```bash
python3 --version
```

### Node.js версия
Убедитесь, что используется Node.js 18+:
```bash
node --version
```

## Логи и отладка

### Включить подробные логи в backend
Измените в `start.py`:
```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="debug"  # Добавьте это
)
```

### Включить логи в frontend
Добавьте в `src/services/api.ts`:
```typescript
apiClient.interceptors.request.use(request => {
  console.log('Request:', request);
  return request;
});

apiClient.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

## Быстрая диагностика

Запустите этот скрипт для проверки всех компонентов:

```bash
echo "🔍 Проверка backend..."
curl -s http://localhost:8000/health && echo " ✅ Backend работает" || echo " ❌ Backend не отвечает"

echo "🔍 Проверка API..."
curl -s 'http://localhost:8000/api/providers?limit=1' > /dev/null && echo " ✅ API работает" || echo " ❌ API не отвечает"

echo "🔍 Проверка портов..."
lsof -ti:8000 > /dev/null && echo " ✅ Порт 8000 занят (backend запущен)" || echo " ⚠️  Порт 8000 свободен (backend не запущен)"
lsof -ti:5173 > /dev/null && echo " ✅ Порт 5173 занят (frontend запущен)" || echo " ⚠️  Порт 5173 свободен (frontend не запущен)"
```

## Получение помощи

Если проблема не решена:

1. Соберите информацию:
   - Скриншот консоли браузера (F12 → Console)
   - Скриншот Network tab (F12 → Network)
   - Логи из терминала, где запущен backend
   - Логи из терминала, где запущен frontend

2. Проверьте документацию:
   - `README.md` - общая информация
   - `START.md` - инструкции по запуску
   - `ARCHITECTURE.md` - архитектура проекта
