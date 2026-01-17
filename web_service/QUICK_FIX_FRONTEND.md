# 🚀 Быстрое решение проблемы с пустым frontend

## Проблема
`http://localhost:5173/` показывает пустую страницу

## Решение

### 1. Создайте файл `.env` в директории frontend

```bash
cd web_service/frontend
echo "VITE_API_URL=http://localhost:8000/api" > .env
```

### 2. Убедитесь, что backend запущен

```bash
# Проверка
curl http://localhost:8000/health

# Если не запущен, запустите:
cd web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Запустите frontend

```bash
cd web_service/frontend
npm run dev
```

**Важно:** После создания `.env` файла перезапустите frontend сервер!

### 4. Проверьте в браузере

1. Откройте `http://localhost:5173/`
2. Нажмите F12 для открытия DevTools
3. Проверьте вкладку **Console** на наличие ошибок
4. Проверьте вкладку **Network** - должны быть запросы к `/api/providers`

---

## Если проблема сохраняется

### Проверьте консоль браузера (F12)

**Ошибка:** `ERR_CONNECTION_REFUSED`
- Backend не запущен → запустите backend

**Ошибка:** `CORS policy`
- Проверьте, что `http://localhost:5173` в списке CORS_ORIGINS в backend конфиге

**Ошибка:** `Failed to fetch`
- Проверьте, что backend отвечает: `curl http://localhost:8000/api/providers?limit=1`

---

## Быстрая проверка

```bash
# Терминал 1: Backend (должен быть запущен)
cd web_service/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2: Frontend
cd web_service/frontend
npm run dev
```

После запуска обоих сервисов откройте `http://localhost:5173/` в браузере.
