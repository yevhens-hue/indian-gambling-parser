# 🖥️ Локальный запуск (без Docker)

## ⚡ Быстрый старт

```bash
cd web_service
./start_local.sh
```

Это автоматически:
- ✅ Проверит зависимости
- ✅ Установит их при необходимости
- ✅ Запустит backend на http://localhost:8000
- ✅ Опционально запустит frontend на http://localhost:5173

---

## 📋 Что нужно

- **Python 3.10+** (для backend)
- **Node.js 18+** (для frontend, опционально)
- **Google Sheets credentials** (для импорта, опционально)

---

## 🚀 Запуск вручную

### Backend

```bash
cd web_service/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 start.py
```

### Frontend (в другом терминале)

```bash
cd web_service/frontend
npm install
npm run dev
```

---

## 🧪 Тест импорта

```bash
# Предпросмотр
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"

# Импорт
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

---

**Подробная инструкция:** `LOCAL_RUN.md`
