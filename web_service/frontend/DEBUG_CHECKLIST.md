# 🔍 Чеклист для отладки пустой страницы

## ✅ Что проверить в DevTools (F12)

### 1. Вкладка Console (важно!)
- Откройте вкладку **Console**
- Проверьте наличие ошибок (красные сообщения)
- Типичные ошибки:
  - `Failed to fetch` - проблема подключения к backend
  - `Cannot find module` - проблема с импортами
  - `Uncaught TypeError` - ошибка выполнения кода
  - `CORS error` - проблема с CORS

### 2. Вкладка Network
- Откройте вкладку **Network**
- Обновите страницу (F5)
- Проверьте запросы:
  - `main.tsx` - должен загружаться со статусом 200
  - `/api/providers` - должен быть запрос к API
  - Если запросов к `/api/providers` нет - значит React не запускается
  - Если есть ошибки 404/500 - проблема с backend

### 3. Вкладка Sources
- Проверьте, что файлы загружаются
- `main.tsx` должен быть виден в списке файлов
- `App.tsx` должен быть виден

## 🐛 Типичные проблемы и решения

### Проблема: В Console есть ошибка "Failed to fetch" или "Network Error"

**Решение:**
1. Проверьте, что backend запущен:
   ```bash
   curl http://localhost:8000/health
   ```
2. Проверьте файл `.env` в `web_service/frontend/`:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```
3. Если изменили .env, перезапустите frontend

### Проблема: В Console ошибка "Cannot find module '...'"

**Решение:**
```bash
cd web_service/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Проблема: В Network нет запросов к `/api/providers`

**Причина:** React приложение не запускается или есть ошибка JavaScript

**Решение:**
1. Проверьте Console на наличие ошибок
2. Проверьте, что `main.tsx` загружается (статус 200 в Network)
3. Проверьте Sources - должен быть виден код `App.tsx`

### Проблема: В Network запрос к `/api/providers` возвращает 404

**Решение:**
1. Проверьте URL в запросе (должен быть `http://localhost:8000/api/providers`)
2. Проверьте, что backend запущен на порту 8000
3. Проверьте `web_service/backend/app/main.py` - правильный ли префикс API

### Проблема: В Network запрос к `/api/providers` возвращает CORS error

**Решение:**
1. Проверьте `web_service/backend/app/main.py`
2. Убедитесь, что в `CORS_ORIGINS` есть `http://localhost:5173`
3. Перезапустите backend

## 📝 Быстрая диагностика

Выполните в терминале:

```bash
# Проверка backend
echo "Backend health:"
curl -s http://localhost:8000/health || echo "❌ Backend не отвечает"

# Проверка API
echo -e "\nAPI test:"
curl -s 'http://localhost:8000/api/providers?limit=1' | head -5 || echo "❌ API не отвечает"

# Проверка портов
echo -e "\nПорты:"
lsof -ti:8000 && echo "✅ Backend на порту 8000" || echo "❌ Backend не запущен"
lsof -ti:5173 && echo "✅ Frontend на порту 5173" || echo "❌ Frontend не запущен"
```

## 🎯 Следующие шаги

После проверки Console:

1. **Если есть ошибки** - скопируйте текст ошибки и сообщите
2. **Если ошибок нет, но страница пустая** - проверьте Network tab
3. **Если запросы к API есть, но данные не приходят** - проверьте ответ API (кликните на запрос в Network)
