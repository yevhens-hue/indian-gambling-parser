# 🖥️ Локальный запуск без Docker

## ✅ Быстрый старт (без Docker)

### Вариант 1: Автоматический скрипт (рекомендуется)

```bash
cd web_service
./start_local.sh
```

Этот скрипт:
- ✅ Проверит зависимости
- ✅ Создаст виртуальное окружение (если нужно)
- ✅ Установит зависимости
- ✅ Запустит backend на http://localhost:8000
- ✅ Опционально запустит frontend на http://localhost:5173

---

### Вариант 2: Ручной запуск

#### 1. Backend

```bash
cd web_service/backend

# Создать виртуальное окружение (если еще нет)
python3 -m venv venv
source venv/bin/activate  # На macOS/Linux
# или
# venv\Scripts\activate  # На Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить
python3 start.py
```

Backend будет доступен на: http://localhost:8000

#### 2. Frontend (в другом терминале)

```bash
cd web_service/frontend

# Установить зависимости (если еще нет)
npm install

# Запустить
npm run dev
```

Frontend будет доступен на: http://localhost:5173

---

## 🧪 Тестирование импорта данных

После запуска backend, можно протестировать импорт:

### Предпросмотр данных

```bash
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"
```

### Импорт данных

```bash
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Через веб-интерфейс

1. Откройте http://localhost:5173
2. Найдите блок "Импорт данных из Google Sheets"
3. Нажмите "Импортировать"

---

## 📋 Требования

### Backend
- Python 3.10+
- pip
- Виртуальное окружение (создается автоматически)

### Frontend (опционально)
- Node.js 18+
- npm

### Google Sheets API (для импорта)
- Файл `google_credentials.json` в корне проекта
- Service Account настроен и имеет доступ к таблице

---

## 🔧 Настройка

### Переменные окружения

Создайте файл `backend/.env` (опционально):

```bash
SECRET_KEY=your-secret-key
AUTH_ENABLED=false
DB_PATH=../../providers_data.db
GOOGLE_SHEET_ID=1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
GOOGLE_CREDENTIALS_PATH=../../google_credentials.json
```

Или используйте значения по умолчанию из `config.py`.

---

## 🐛 Troubleshooting

### Порт 8000 уже занят

```bash
# Найти процесс
lsof -ti:8000

# Остановить процесс
lsof -ti:8000 | xargs kill -9

# Или использовать скрипт start.sh
cd web_service/backend
./start.sh
```

### Ошибка импорта модулей

```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Google Sheets не работает

```bash
# Проверьте наличие файла
ls ../../google_credentials.json

# Проверьте доступ
cd backend
python3 test_import_1win.py
```

---

## 📚 Полезные команды

### Остановка сервисов

```bash
# Найти процессы
ps aux | grep "python3 start.py"
ps aux | grep "npm run dev"

# Остановить по PID
kill <PID>

# Или используйте Ctrl+C в терминале где запущены
```

### Просмотр логов

Логи отображаются прямо в терминале. Для backend можно также использовать:

```bash
tail -f backend/logs/app.log  # если логирование настроено
```

### Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# API endpoints
curl http://localhost:8000/api/providers?limit=1

# API документация
open http://localhost:8000/docs
```

---

## 🚀 Установка Docker (опционально)

Если хотите использовать Docker в будущем:

### macOS

```bash
# Через Homebrew
brew install --cask docker

# Или скачайте Docker Desktop
# https://www.docker.com/products/docker-desktop
```

### Linux (Ubuntu/Debian)

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перезапустить сессию или выполнить:
newgrp docker
```

После установки Docker:

```bash
cd web_service
./deploy_production.sh
```

---

## ✅ Проверка готовности

### Быстрый тест

```bash
cd web_service

# Тест backend
cd backend
python3 test_import_1win.py

# Тест API (если backend запущен)
cd ..
python3 backend/test_api_import.py
```

---

## 🎯 Резюме

**Для локального запуска без Docker:**

```bash
cd web_service
./start_local.sh
```

Или вручную:
```bash
# Terminal 1: Backend
cd web_service/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 start.py

# Terminal 2: Frontend (опционально)
cd web_service/frontend
npm install
npm run dev
```

**Готово! 🚀**
