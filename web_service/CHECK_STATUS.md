# ✅ Проверка статуса веб-сервиса

## 🟢 Текущий статус

### Frontend
- ✅ **Запущен** на http://localhost:5173/
- Статус: Работает

### Backend  
- ✅ **Запущен** на http://localhost:8000
- Health check: OK
- API Docs: http://localhost:8000/docs

## 🌐 Откройте в браузере

**Frontend приложение:**
```
http://localhost:5173
```

**API Документация (Swagger UI):**
```
http://localhost:8000/docs
```

**Альтернативная документация (ReDoc):**
```
http://localhost:8000/redoc
```

## 📋 Что вы увидите

1. **Главная страница** (http://localhost:5173):
   - Статистика по провайдерам
   - Фильтры для поиска
   - Таблица с данными
   - Кнопки экспорта

2. **API Документация** (http://localhost:8000/docs):
   - Интерактивная документация всех endpoints
   - Возможность тестировать API прямо в браузере

## 🔍 Проверка работы

### Проверить Backend API:
```bash
curl http://localhost:8000/health
# Должен вернуть: {"status":"ok"}

curl 'http://localhost:8000/api/providers?limit=5'
# Должен вернуть JSON с провайдерами
```

### Проверить Frontend:
- Откройте http://localhost:5173 в браузере
- Должна загрузиться страница с таблицей данных
- Проверьте консоль браузера (F12) на ошибки

## 🐛 Если что-то не работает

### Frontend показывает ошибки в консоли:
1. Убедитесь, что backend запущен: `curl http://localhost:8000/health`
2. Проверьте CORS настройки (должны быть разрешены localhost:5173)
3. Проверьте Network tab в DevTools - должны быть запросы к `/api/providers`

### Таблица пустая:
1. Проверьте, что в БД есть данные: 
   ```bash
   python3 main_parser_playwright.py --show-results
   ```
2. Проверьте ответ API:
   ```bash
   curl 'http://localhost:8000/api/providers?limit=10'
   ```

### Backend не отвечает:
1. Проверьте, что процесс запущен:
   ```bash
   lsof -ti:8000
   ```
2. Проверьте логи в терминале, где запущен backend
3. Попробуйте перезапустить: `./stop.sh && ./start.sh`

## 🎉 Все готово!

Ваш веб-сервис полностью настроен и готов к работе!
