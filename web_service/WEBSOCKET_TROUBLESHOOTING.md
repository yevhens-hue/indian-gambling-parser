# 🔧 Устранение проблем с WebSocket

## ✅ Исправленные проблемы

### 1. WebSocket подключение падает при первом подключении
**Решение:** Добавлена задержка перед первым подключением и улучшена обработка ошибок.

### 2. Множественные попытки переподключения
**Решение:** Улучшена логика переподключения с экспоненциальной задержкой и ограничением попыток.

### 3. Неправильный URL WebSocket
**Решение:** URL теперь автоматически формируется на основе VITE_API_URL.

---

## 🐛 Частые проблемы и решения

### Проблема: "WebSocket is closed before the connection is established"

**Причины:**
- Backend еще не запущен
- Backend не поддерживает WebSocket upgrade
- Неправильный URL WebSocket
- Проблемы с CORS

**Решение:**
1. Проверьте, что backend запущен:
   ```bash
   curl http://localhost:8000/health
   ```

2. Проверьте WebSocket endpoint:
   ```bash
   # Установите wscat (npm install -g wscat)
   wscat -c ws://localhost:8000/api/ws/updates
   ```

3. Проверьте логи backend:
   ```bash
   # Если используете start.py
   tail -f backend/logs/*.log
   ```

4. Убедитесь, что WebSocket endpoint включен в main.py

### Проблема: Множественные попытки переподключения в консоли

**Это нормально!** WebSocket автоматически пытается переподключиться при потере соединения.

**Если переподключений слишком много:**
- Проверьте стабильность сети
- Проверьте, что backend не падает
- Увеличьте интервал между попытками (в useWebSocket.ts)

### Проблема: "Slow network is detected"

**Причины:**
- Медленное интернет-соединение
- Backend отвечает медленно
- Большой размер данных

**Решение:**
- Это предупреждение браузера, не критичная ошибка
- Проверьте производительность backend
- Оптимизируйте размер передаваемых данных
- Используйте компрессию для WebSocket (если возможно)

### Проблема: "Unchecked runtime.lastError"

**Причина:** Ошибка связана с расширениями браузера (не с нашим кодом).

**Решение:**
- Это предупреждение от расширений браузера (React DevTools, etc.)
- Можно игнорировать, не влияет на работу приложения

---

## 🔍 Диагностика

### Проверка WebSocket подключения

**1. Проверка через браузер:**
```javascript
// В консоли браузера (F12)
const ws = new WebSocket('ws://localhost:8000/api/ws/updates');
ws.onopen = () => console.log('✅ Подключено');
ws.onerror = (e) => console.error('❌ Ошибка:', e);
ws.onmessage = (msg) => console.log('📨 Сообщение:', msg.data);
```

**2. Проверка через curl (если поддерживается):**
```bash
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: test" \
     --header "Sec-WebSocket-Version: 13" \
     http://localhost:8000/api/ws/updates
```

**3. Проверка через wscat:**
```bash
# Установка
npm install -g wscat

# Подключение
wscat -c ws://localhost:8000/api/ws/updates
```

---

## ⚙️ Настройка

### Изменение URL WebSocket

**Через переменные окружения:**
```bash
# В frontend/.env
VITE_WS_URL=ws://your-server.com/api/ws/updates
```

**Или в коде (useWebSocket.ts):**
```typescript
const WS_URL = 'ws://your-custom-url/api/ws/updates';
```

### Настройка интервалов переподключения

В `useWebSocket.ts`:
```typescript
const maxReconnectAttempts = 5; // Максимум попыток
const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // Экспоненциальная задержка
```

### Отключение WebSocket (если не нужен)

В `App.tsx`:
```typescript
// Закомментируйте или удалите:
// const { isConnected, lastUpdate } = useWebSocket();
```

---

## ✅ Чеклист для проверки

- [ ] Backend запущен и отвечает на `/health`
- [ ] WebSocket endpoint доступен на `/api/ws/updates`
- [ ] Нет ошибок в логах backend
- [ ] CORS настроен правильно (для WebSocket)
- [ ] URL WebSocket правильный (ws:// или wss://)
- [ ] Нет блокировки WebSocket файрволом/прокси
- [ ] Браузер поддерживает WebSocket (все современные браузеры)

---

## 📊 Мониторинг

### Проверка активных подключений

В backend логи вы увидите:
```
✅ WebSocket подключен. Всего подключений: 1
❌ WebSocket отключен. Осталось подключений: 0
```

### Проверка через API

```bash
# Получить количество активных подключений (если endpoint есть)
curl http://localhost:8000/api/ws/stats
```

---

## 🚀 Production настройки

### Использование WSS (WebSocket Secure)

Для production используйте `wss://` вместо `ws://`:

```bash
# frontend/.env.production
VITE_WS_URL=wss://your-domain.com/api/ws/updates
```

### Настройка reverse proxy (nginx)

```nginx
location /api/ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

---

## 📚 Дополнительные ресурсы

- **FastAPI WebSocket docs:** https://fastapi.tiangolo.com/advanced/websockets/
- **MDN WebSocket API:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **React WebSocket hooks:** https://github.com/robtaussig/react-use-websocket

---

**Если проблемы остаются, проверьте логи backend и frontend для более детальной информации!**
