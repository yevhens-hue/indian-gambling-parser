# ⚡ Быстрый старт БЕЗ Docker

## 🚀 Запуск всего за 1 команду

```bash
cd web_service
./start_local.sh
```

Скрипт автоматически:
- ✅ Проверит и установит зависимости
- ✅ Запустит backend на http://localhost:8000
- ✅ Опционально запустит frontend на http://localhost:5173

---

## 📋 Или вручную (2 команды)

### Terminal 1: Backend
```bash
cd web_service/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 start.py
```

### Terminal 2: Frontend (опционально)
```bash
cd web_service/frontend
npm install
npm run dev
```

---

## 🧪 Тест импорта данных 1win IN

После запуска backend:

```bash
# Предпросмотр (335 записей)
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"

# Импорт
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

Или через веб-интерфейс:
- Откройте http://localhost:5173
- Найдите блок "Импорт данных из Google Sheets"
- Нажмите "Импортировать"

---

## ✅ Что уже работает

- ✅ Backend запущен на порту 8000 (проверено)
- ✅ Импорт данных работает (335 записей найдено)
- ✅ API endpoints доступны
- ✅ Все зависимости установлены

---

**Подробнее:** `web_service/LOCAL_RUN.md`
