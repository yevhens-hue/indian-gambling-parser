# 🚀 Быстрый запуск фронтенда

## Проблема: ERR_CONNECTION_REFUSED на localhost:5173

Это означает, что фронтенд сервер не запущен.

## ✅ Решение: Запустить фронтенд

### Вариант 1: Через npm (рекомендуется)

```bash
cd web_service/frontend
npm install  # Если зависимости не установлены
npm run dev  # Запуск dev сервера
```

Фронтенд будет доступен на `http://localhost:5173`

### Вариант 2: Через скрипт start_local.sh

```bash
cd web_service
./start_local.sh
```

Этот скрипт запускает и backend, и frontend.

### Вариант 3: Только фронтенд (если backend уже запущен)

```bash
cd web_service/frontend
npm run dev
```

## 🔧 Проверка

После запуска вы должны увидеть:
```
  VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## ⚠️ Важно

- Backend должен быть запущен на `http://localhost:8000`
- Убедитесь, что порт 5173 не занят другим процессом
- Если порт занят, Vite автоматически предложит использовать другой порт

## 🛑 Остановка

Нажмите `Ctrl+C` в терминале где запущен фронтенд.

## 📝 Полная инструкция

Для полной инструкции см.:
- `web_service/QUICK_START.md` - быстрый старт всего сервиса
- `web_service/LOCAL_RUN.md` - локальный запуск без Docker
