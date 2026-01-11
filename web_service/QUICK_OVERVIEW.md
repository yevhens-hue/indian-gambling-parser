# ⚡ Краткий обзор работы сервиса

## 🎯 Что делает сервис?

Собирает и отображает информацию о платежных провайдерах с гемблинговых сайтов Индии (1win, Betway, и др.).

---

## 📦 Компоненты

### 1. Парсер (Python Playwright)
**Что делает:** Автоматически логинится на сайты, находит провайдеров, делает скриншоты

**Как:**
1. Открывает сайт → логинится
2. Переходит в кассир (Cashier)
3. Находит раздел E-WALLETS
4. Для каждого провайдера:
   - Кликает → открывает форму оплаты
   - Делает скриншот
   - Извлекает URL, домен, название
   - Сохраняет в базу данных

**Результат:** `providers_data.db` + скриншоты в `screenshots/`

---

### 2. Backend API (FastAPI)
**Что делает:** Предоставляет REST API и WebSocket для работы с данными

**Endpoints:**
- `GET /api/providers` - список провайдеров (фильтры, пагинация)
- `GET /api/analytics/dashboard` - аналитика
- `POST /api/import/google-sheets` - импорт из Google Sheets
- `WS /ws/updates` - real-time обновления

**Как работает:**
- Читает данные из SQLite
- Применяет фильтры/сортировку/пагинацию
- Отправляет JSON клиенту
- WebSocket каждые 5 сек проверяет изменения → отправляет обновления

---

### 3. Frontend (React)
**Что делает:** Красивый веб-интерфейс для просмотра и управления данными

**Возможности:**
- 📊 Таблица с данными (пагинация, сортировка, фильтры)
- 📈 Графики статистики (мерчанты, типы аккаунтов, методы оплаты)
- 📱 Dashboard аналитики (метрики, тренды, распределения)
- 📥 Импорт из Google Sheets
- 📤 Экспорт в XLSX/CSV/JSON
- 🔄 Real-time обновления (WebSocket)

---

## 🔄 Поток данных

```
Парсер → SQLite → Backend API → Frontend → Пользователь
                ↓
           Google Sheets (импорт/экспорт)
```

### Детальный поток:

1. **Парсер собирает данные:**
   ```
   Playwright → Логин → Кассир → Провайдеры → SQLite
   ```

2. **Backend предоставляет API:**
   ```
   SQLite → StorageAdapter → FastAPI → JSON → Frontend
   ```

3. **Frontend отображает:**
   ```
   React Query → API запрос → DataTable/Graphs/Dashboard
   ```

4. **Real-time обновления:**
   ```
   Backend (каждые 5 сек) → Проверка БД → WebSocket → Frontend → Автообновление
   ```

---

## 🚀 Основные сценарии использования

### Сценарий 1: Сбор данных
```bash
python main_parser_playwright.py --merchant 1win
```
→ Парсер собирает данные → Сохраняет в SQLite → Экспортирует в XLSX

### Сценарий 2: Просмотр в веб-интерфейсе
```
Открыть http://localhost:5173
→ Вижу таблицу с данными
→ Применяю фильтры (merchant=1win)
→ Вижу графики статистики
→ Экспортирую в CSV
```

### Сценарий 3: Импорт из Google Sheets
```
Ввожу GID листа → Предпросмотр → Импорт
→ Backend парсит Google Sheets → Сохраняет в SQLite
→ Frontend автоматически обновляется (WebSocket)
```

### Сценарий 4: Аналитика
```
Переключаюсь на Dashboard
→ Вижу метрики (всего провайдеров, новых сегодня)
→ Вижу графики трендов
→ Меняю период (7/30/90 дней)
```

---

## 🗂️ Структура данных

**Таблица `providers`:**
- `merchant` - мерчант (1win, betway)
- `merchant_domain` - домен (1win.in)
- `provider_domain` - домен провайдера (paytm.com)
- `provider_name` - название провайдера
- `account_type` - тип аккаунта (FTD)
- `payment_method` - метод оплаты (UPI)
- `final_url` - URL формы оплаты
- `screenshot_path` - путь к скриншоту
- `is_iframe` - форма в iframe?
- `requires_otp` - требуется OTP?
- `timestamp_utc` - время добавления

---

## 🛠️ Технологии

**Backend:**
- FastAPI (REST API)
- SQLite (БД)
- Playwright (парсер)
- WebSockets (real-time)
- gspread (Google Sheets)

**Frontend:**
- React 18 + TypeScript
- Material-UI (компоненты)
- React Query (данные)
- Recharts (графики)

**Deployment:**
- Docker & Docker Compose
- Nginx (опционально)

---

## 📊 Производительность

- **Серверная пагинация** - не загружает все данные сразу
- **Виртуализация** - DataGrid рендерит только видимые строки
- **React Query кэш** - кэширует запросы
- **WebSocket оптимизация** - проверка изменений каждые 5 сек

---

## 🔐 Безопасность

- JWT авторизация (опционально)
- CORS настройка
- Валидация данных через Pydantic
- Хеширование паролей (bcrypt)

---

## 📝 Конфигурация

**merchants_config.py:**
- Креденшиалы для входа
- CSS селекторы
- Настройки провайдеров

**Environment variables:**
- `DB_PATH` - путь к БД
- `GOOGLE_SHEET_ID` - ID Google таблицы
- `GOOGLE_CREDENTIALS_PATH` - путь к credentials

---

**Полная документация:** `HOW_IT_WORKS.md`
