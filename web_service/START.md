# 🚀 Инструкция по запуску веб-сервиса

## Шаг 1: Проверка зависимостей

Убедитесь, что установлены:
- Python 3.8+
- Node.js 18+
- npm или yarn

## Шаг 2: Установка зависимостей Backend

```bash
cd web_service/backend
pip install -r requirements.txt
```

Или установите в виртуальном окружении:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Шаг 3: Установка зависимостей Frontend

```bash
cd web_service/frontend
npm install
```

## Шаг 4: Проверка данных

Убедитесь, что у вас есть:
- Файл `providers_data.db` в корне проекта (создается парсером)
- Файл `storage.py` в корне проекта

Если данных нет, запустите парсер:
```bash
python main_parser_playwright.py --show-results
```

## Шаг 5: Запуск Backend

Откройте первый терминал:

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser/web_service/backend
python3 start.py
```

**На macOS:** Используйте `python3` вместо `python`

Или напрямую:
```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

Или через скрипт (если настроен):
```bash
./start.py
```

Backend будет доступен на:
- API: http://localhost:8000/api
- Документация: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Шаг 6: Запуск Frontend

Откройте второй терминал:

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser/web_service/frontend
npm run dev
```

Frontend будет доступен на: http://localhost:5173

## ✅ Готово!

Откройте браузер и перейдите на http://localhost:5173

Вы должны увидеть:
- Статистику по провайдерам
- Фильтры для поиска
- Таблицу с данными
- Кнопки экспорта

## 🐛 Решение проблем

### Backend не запускается

**Ошибка: ModuleNotFoundError: No module named 'storage'**

Решение: Убедитесь, что вы находитесь в правильной директории и что файл `storage.py` существует в корне проекта.

**Ошибка: No such file or directory: 'providers_data.db'**

Решение: Запустите парсер для создания БД, или создайте пустую БД:
```bash
python -c "from storage import Storage; s = Storage(); print('DB created')"
```

### Frontend не подключается к Backend

**Ошибка: Network Error или CORS**

Решение:
1. Убедитесь, что backend запущен на порту 8000
2. Проверьте `frontend/.env` - должно быть: `VITE_API_URL=http://localhost:8000/api`
3. Проверьте CORS настройки в `backend/app/main.py`

**Ошибка: 404 Not Found**

Решение:
- Проверьте, что backend отвечает: откройте http://localhost:8000/docs
- Проверьте URL в `frontend/src/services/api.ts`

### Таблица пустая

Решение:
1. Проверьте, что в БД есть данные: `python main_parser_playwright.py --show-results`
2. Проверьте консоль браузера на ошибки (F12)
3. Проверьте Network tab в DevTools - должны быть запросы к `/api/providers`

## 📝 Полезные команды

### Просмотр логов Backend
Логи отображаются в терминале, где запущен backend.

### Просмотр логов Frontend
Откройте DevTools в браузере (F12) → Console

### Перезапуск после изменений

Backend автоматически перезапускается при изменении файлов (благодаря `--reload`).

Frontend автоматически перезагружается при изменении файлов (Hot Module Replacement).

## 🔧 Настройка портов

Если порты 8000 или 5173 заняты, измените:

**Backend:**
```bash
uvicorn app.main:app --reload --port 8001
```
И обновите `frontend/.env`:
```env
VITE_API_URL=http://localhost:8001/api
```

**Frontend:**
В `frontend/vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 5174
  }
})
```
