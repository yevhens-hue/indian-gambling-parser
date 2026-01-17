# 🔍 Решение проблем с пустым frontend

Если `http://localhost:5173/` показывает пустую страницу, выполните следующие шаги диагностики:

## 1. Проверка запущенных сервисов

### Проверка backend (порт 8000)

```bash
# Проверка, запущен ли backend
lsof -i :8000

# Или
curl http://localhost:8000/health
```

**Если backend не запущен:**
```bash
cd web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Проверка frontend (порт 5173)

```bash
# Проверка, запущен ли frontend
lsof -i :5173

# Если не запущен:
cd web_service/frontend
npm run dev
```

---

## 2. Проверка консоли браузера

Откройте DevTools (F12) и проверьте вкладку **Console** на наличие ошибок:

### Типичные ошибки:

#### ❌ `ERR_CONNECTION_REFUSED`
**Причина:** Backend не запущен или недоступен

**Решение:**
```bash
cd web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### ❌ `CORS policy: No 'Access-Control-Allow-Origin'`
**Причина:** Проблема с CORS настройками

**Решение:** Проверьте `web_service/backend/app/config.py`:
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # ← Должен быть этот адрес
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
```

#### ❌ `Failed to fetch` или `Network Error`
**Причина:** Backend не отвечает или неправильный URL

**Решение:** 
1. Проверьте, что backend запущен
2. Проверьте переменную окружения `VITE_API_URL` в frontend

---

## 3. Проверка переменных окружения

### Frontend (.env файл)

Создайте файл `web_service/frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000/api
```

**Важно:** После изменения `.env` перезапустите frontend сервер!

```bash
# Остановите сервер (Ctrl+C) и запустите снова
cd web_service/frontend
npm run dev
```

---

## 4. Проверка API подключения

### Тест подключения к backend:

```bash
# Health check
curl http://localhost:8000/health

# Проверка API
curl http://localhost:8000/api/providers?limit=1
```

Если эти команды не работают, backend не запущен или неправильно настроен.

---

## 5. Проверка структуры HTML

Откройте DevTools → Elements и проверьте:

1. **Есть ли элемент `<div id="root">`?**
   - Если нет → проблема с `index.html`
   
2. **Есть ли содержимое внутри `#root`?**
   - Если пусто → проблема с React рендерингом
   - Проверьте Console на ошибки JavaScript

3. **Есть ли ошибки загрузки скриптов?**
   - Проверьте вкладку Network в DevTools
   - Ищите файлы с статусом 404 или ошибками загрузки

---

## 6. Быстрая диагностика

Выполните этот скрипт для проверки всех компонентов:

```bash
#!/bin/bash

echo "🔍 Проверка сервисов..."
echo ""

# Backend
echo "Backend (порт 8000):"
if lsof -i :8000 > /dev/null 2>&1; then
    echo "  ✅ Запущен"
    curl -s http://localhost:8000/health | head -1
else
    echo "  ❌ Не запущен"
    echo "  Запустите: cd web_service/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

echo ""

# Frontend
echo "Frontend (порт 5173):"
if lsof -i :5173 > /dev/null 2>&1; then
    echo "  ✅ Запущен"
else
    echo "  ❌ Не запущен"
    echo "  Запустите: cd web_service/frontend && npm run dev"
fi

echo ""

# API тест
echo "API тест:"
if curl -s http://localhost:8000/api/providers?limit=1 > /dev/null 2>&1; then
    echo "  ✅ API доступен"
else
    echo "  ❌ API недоступен"
fi
```

---

## 7. Пошаговый запуск

### Шаг 1: Запуск backend

```bash
# Терминал 1
cd web_service/backend

# Проверьте наличие .env файла или создайте его
cat > .env << EOF
ENVIRONMENT=development
JWT_SECRET_KEY=dev-secret-key-change-in-production
AUTH_ENABLED=false
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF

# Запустите backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Ожидаемый вывод:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Шаг 2: Запуск frontend

```bash
# Терминал 2
cd web_service/frontend

# Проверьте наличие .env файла
cat > .env << EOF
VITE_API_URL=http://localhost:8000/api
EOF

# Установите зависимости (если еще не установлены)
npm install

# Запустите frontend
npm run dev
```

**Ожидаемый вывод:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Шаг 3: Проверка в браузере

1. Откройте `http://localhost:5173/`
2. Откройте DevTools (F12)
3. Проверьте вкладку **Console**
4. Проверьте вкладку **Network**

---

## 8. Типичные проблемы и решения

### Проблема: Страница полностью белая

**Возможные причины:**
1. JavaScript ошибка в консоли
2. Backend не запущен
3. Неправильный API URL

**Решение:**
1. Откройте DevTools → Console
2. Найдите ошибки (красные сообщения)
3. Проверьте, что backend запущен: `curl http://localhost:8000/health`

### Проблема: Видно только заголовок, но нет данных

**Возможные причины:**
1. Backend запущен, но база данных пуста
2. Ошибка при загрузке данных из API

**Решение:**
1. Проверьте Network tab в DevTools
2. Найдите запрос к `/api/providers`
3. Проверьте ответ сервера
4. Если база пуста, запустите парсер для сбора данных

### Проблема: CORS ошибки

**Решение:**
1. Проверьте `web_service/backend/app/config.py`
2. Убедитесь, что `http://localhost:5173` в списке `CORS_ORIGINS`
3. Перезапустите backend после изменения конфига

---

## 9. Проверка логов

### Backend логи

Backend выводит логи в консоль. Ищите:
- `INFO:     Application startup complete.` - успешный запуск
- `ERROR` или `WARNING` - проблемы

### Frontend логи

В браузере DevTools → Console:
- Ошибки загрузки модулей
- Ошибки API запросов
- React ошибки рендеринга

---

## 10. Полная переустановка (если ничего не помогает)

```bash
# Backend
cd web_service/backend
pip install --upgrade -r requirements.txt

# Frontend
cd web_service/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## ✅ Чеклист диагностики

- [ ] Backend запущен на порту 8000
- [ ] Frontend запущен на порту 5173
- [ ] `curl http://localhost:8000/health` возвращает ответ
- [ ] `curl http://localhost:8000/api/providers?limit=1` работает
- [ ] В браузере нет ошибок в Console
- [ ] В браузере нет ошибок в Network tab
- [ ] Файл `web_service/frontend/.env` существует с правильным `VITE_API_URL`
- [ ] CORS настроен правильно в `web_service/backend/app/config.py`

---

Если проблема не решена, проверьте логи и ошибки в консоли браузера (F12).
