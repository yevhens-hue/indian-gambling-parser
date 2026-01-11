# 🔧 Как работает сервис - Полное описание

## 📋 Общая архитектура

Сервис состоит из **трех основных компонентов**:

1. **Парсер данных** (Python Playwright) - сбор данных с сайтов
2. **Backend API** (FastAPI) - обработка и хранение данных
3. **Frontend веб-интерфейс** (React) - отображение и управление данными

```
┌─────────────────┐
│   Парсер        │ → Собирает данные с сайтов
│  (Playwright)   │ → Сохраняет в SQLite/XLSX
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   База данных   │ ← SQLite (providers_data.db)
│   (SQLite)      │ ← XLSX (providers_data.xlsx)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Backend API   │ ←──→│  Frontend       │
│   (FastAPI)     │     │  (React)        │
│                 │     │                 │
│ - REST API      │     │ - Таблица данных│
│ - WebSocket     │     │ - Графики       │
│ - Импорт/Экспорт│     │ - Фильтры       │
│ - Аналитика     │     │ - Dashboard     │
└─────────────────┘     └─────────────────┘
```

---

## 1. 🔍 Парсер данных (Playwright)

### Назначение
Автоматический сбор информации о платежных провайдерах с гемблинговых сайтов.

### Как работает

#### Шаг 1: Инициализация
```python
parser = ProviderParserPlaywright(headless=False)
```
- Создает директории для скриншотов, cookies, traces
- Инициализирует Storage для сохранения данных

#### Шаг 2: Логин на сайт мерчанта
```python
await parser.login(merchant_url, config)
```
- Открывает браузер (Playwright)
- Переходит на сайт мерчанта
- Находит кнопку входа по CSS селекторам из `merchants_config.py`
- Вводит логин/пароль
- Сохраняет cookies в `storage_states/` для повторного использования

**Конфигурация** (`merchants_config.py`):
```python
MERCHANTS = {
    "1win": {
        "credentials": {"username": "...", "password": "..."},
        "selectors": {
            "login_button": "a[href*='login']",
            "username_input": "input[name='login']",
            ...
        }
    }
}
```

#### Шаг 3: Переход в кассир (Cashier)
```python
await parser.navigate_to_cashier(page, config)
```
- Ищет ссылку/кнопку кассира
- Переходит на страницу пополнения баланса
- Сохраняет URL кассира

#### Шаг 4: Поиск секции E-WALLETS
```python
await parser.find_ewallets_section(page, config)
```
- Ищет раздел электронных кошельков
- Находит все кнопки/ссылки провайдеров
- Извлекает информацию о каждом провайдере

#### Шаг 5: Обработка каждого провайдера
```python
await parser.process_provider_button(page, provider_info, ...)
```
Для каждого провайдера:
1. **Клик по провайдеру** - открывает форму оплаты
2. **Обработка iframe** - если форма в iframe, переключается на него
3. **Обработка popup** - если открылось новое окно, переключается
4. **Извлечение данных:**
   - URL провайдера (entry_url, final_url)
   - Домен провайдера (нормализация через tldextract)
   - Название провайдера
   - Метод оплаты
   - Скриншот формы (сохраняется в `screenshots/`)
5. **Детекция особенностей:**
   - `is_iframe` - форма в iframe?
   - `requires_otp` - требуется OTP?
   - `blocked_by_geo` - блокируется по гео?
   - `captcha_present` - есть капча?
6. **Сохранение в БД:**
   ```python
   storage.save_provider(
       merchant="1win",
       merchant_domain="1win.in",
       provider_domain="paytm.com",
       ...
   )
   ```

#### Шаг 6: Экспорт данных
- Автоматически экспортирует в XLSX после каждого провайдера
- Опционально экспортирует в Google Sheets

### Особенности парсера

**Human-in-the-loop:**
- Если обнаружена капча, останавливается и ждет ручного ввода
- Позволяет человеку пройти капчу, затем продолжает работу

**Обработка ошибок:**
- Retry механизм для неудачных попыток
- Логирование всех действий
- Trace файлы для отладки (Playwright tracing)

**Хранение состояния:**
- Cookies сохраняются в `storage_states/`
- При повторном запуске использует сохраненные cookies (быстрый вход)

---

## 2. 💾 Хранение данных (Storage)

### База данных SQLite

**Структура таблицы `providers`:**
```sql
CREATE TABLE providers (
    id INTEGER PRIMARY KEY,
    merchant TEXT,                    -- Название мерчанта (1win, betway)
    merchant_domain TEXT,             -- Домен мерчанта (1win.in)
    account_type TEXT,                -- Тип аккаунта (FTD, Regular)
    provider_domain TEXT,             -- Домен провайдера (paytm.com)
    provider_name TEXT,               -- Название провайдера
    provider_entry_url TEXT,          -- URL входа провайдера
    final_url TEXT,                   -- Финальный URL формы оплаты
    cashier_url TEXT,                 -- URL кассира
    screenshot_path TEXT,             -- Путь к скриншоту
    detected_in TEXT,                 -- Где обнаружен (ewallet, button)
    payment_method TEXT,              -- Метод оплаты (UPI, NetBanking)
    is_iframe INTEGER,                -- Форма в iframe? (0/1)
    requires_otp INTEGER,             -- Требуется OTP? (0/1)
    blocked_by_geo INTEGER,           -- Блокируется по гео? (0/1)
    captcha_present INTEGER,          -- Есть капча? (0/1)
    timestamp_utc TIMESTAMP,          -- Время добавления
    UNIQUE(merchant_domain, provider_domain, account_type)
)
```

### Нормализация доменов
```python
def normalize_domain(url: str) -> str:
    # Извлекает eTLD+1: "https://pay.paytm.com/..." → "paytm.com"
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"
```

### Экспорт в XLSX
- Автоматически создается `providers_data.xlsx`
- Обновляется при каждом сохранении провайдера
- Форматирование колонок, заголовки

---

## 3. 🚀 Backend API (FastAPI)

### Архитектура

**Основные модули:**
```
backend/app/
├── main.py              # Точка входа, роутинг
├── config.py            # Конфигурация (CORS, env vars)
├── models/              # Pydantic модели
│   └── provider.py
├── services/            # Бизнес-логика
│   ├── storage_adapter.py
│   └── google_sheets_importer.py
└── api/                 # API endpoints
    ├── providers.py     # CRUD операции
    ├── export.py        # Экспорт данных
    ├── import_api.py    # Импорт из Google Sheets
    ├── analytics.py     # Аналитика
    ├── websocket.py     # Real-time обновления
    ├── screenshots.py   # Просмотр скриншотов
    └── auth.py          # Авторизация (JWT)
```

### API Endpoints

#### 1. Providers API (`/api/providers`)
```python
GET  /api/providers           # Список с фильтрацией, пагинацией, сортировкой
GET  /api/providers/{id}      # Один провайдер по ID
PUT  /api/providers/{id}      # Обновить провайдера
GET  /api/providers/stats/statistics  # Статистика
```

**Фильтрация:**
- По мерчанту: `?merchant=1win`
- По домену провайдера: `?provider_domain=paytm.com`
- По типу аккаунта: `?account_type=FTD`
- По методу оплаты: `?payment_method=UPI`
- Текстовый поиск: `?search=paytm`

**Пагинация:**
- `?skip=0&limit=50` - пропустить 0, взять 50

**Сортировка:**
- `?sort_by=timestamp_utc&sort_order=desc`

#### 2. Export API (`/api/export`)
```python
GET /api/export/xlsx          # Скачать XLSX файл
GET /api/export/csv           # Экспорт в CSV
GET /api/export/json          # Экспорт в JSON
```

#### 3. Import API (`/api/import`)
```python
GET  /api/import/google-sheets/preview  # Предпросмотр данных
POST /api/import/google-sheets          # Импорт из Google Sheets
```

**Как работает импорт:**
1. Подключается к Google Sheets API (через `google_credentials.json`)
2. Читает данные из указанного листа (по GID или имени)
3. Парсит колонки: Method, Account, Links, Screenshot, QR, Bank, UPI ID
4. Извлекает домен провайдера из URL/QR/Bank
5. Создает объекты провайдеров
6. Проверяет дубликаты через `provider_exists()`
7. Сохраняет новые провайдеры через `save_provider()`

#### 4. Analytics API (`/api/analytics`)
```python
GET /api/analytics/dashboard                    # Общая статистика
GET /api/analytics/trends?period=day|week|month # Тренды по времени
GET /api/analytics/comparison?merchants=...     # Сравнение мерчантов
GET /api/analytics/provider-details/{domain}    # Детали по провайдеру
```

**Dashboard возвращает:**
- `total_providers` - всего провайдеров
- `new_today` - новых сегодня
- `new_last_7_days` - новых за 7 дней
- `active_merchants` - активных мерчантов
- `top_merchants` - топ мерчантов
- `top_providers` - топ провайдеров
- `trends` - временные тренды
- `account_types_distribution` - распределение по типам аккаунтов
- `payment_methods_distribution` - распределение по методам оплаты

#### 5. WebSocket API (`/ws/updates`)
```python
WS /ws/updates              # WebSocket подключение
POST /ws/trigger-update     # Принудительное обновление
```

**Как работает WebSocket:**
1. Клиент подключается к `/ws/updates`
2. Backend сохраняет подключение в `ConnectionManager`
3. Фоновая задача каждые 5 секунд проверяет изменения в БД:
   ```python
   current_hash = hash(str([(p.id, p.timestamp) for p in providers]))
   if current_hash != last_hash:
       broadcast({"type": "data_updated", "statistics": ...})
   ```
4. При изменении данных отправляет обновление всем подключенным клиентам
5. Клиент получает JSON с новой статистикой и обновляет UI

**Типы сообщений:**
- `initial_data` - начальные данные при подключении
- `data_updated` - данные обновились
- `manual_update` - принудительное обновление
- `pong` - ответ на `ping`

#### 6. Screenshots API (`/api/screenshots`)
```python
GET /api/screenshots/{path}  # Просмотр скриншота
```

#### 7. Auth API (`/api/auth`) - опционально
```python
POST /api/auth/login         # Вход (JWT токен)
POST /api/auth/register      # Регистрация
GET  /api/auth/me            # Текущий пользователь
```

### Storage Adapter

Адаптер между API и Storage:
```python
class StorageAdapter:
    def __init__(self):
        self.storage = Storage()  # Инициализация storage.py
    
    def get_all_providers(self, filters, skip, limit, sort_by, sort_order):
        # Применяет фильтры
        # Сортирует
        # Пагинирует
        # Возвращает {items: [], total: 100, ...}
```

---

## 4. 🎨 Frontend (React)

### Архитектура

```
frontend/src/
├── App.tsx                 # Главный компонент
├── main.tsx                # Точка входа
├── components/
│   ├── DataTable/         # Таблица данных (Material-UI DataGrid)
│   ├── Filters/           # Фильтры (TextField, Select)
│   ├── ExportButtons/     # Кнопки экспорта
│   ├── Charts/            # Графики статистики (Recharts)
│   ├── Analytics/         # Dashboard аналитики
│   ├── ImportData/        # Импорт из Google Sheets
│   └── ScreenshotViewer/  # Просмотр скриншотов
├── hooks/
│   ├── useProviders.ts    # React Query hook для данных
│   └── useWebSocket.ts    # WebSocket hook
└── services/
    └── api.ts             # API клиент (axios)
```

### Основной поток данных

#### 1. Загрузка данных
```typescript
const { data, isLoading, error } = useProviders(filters, pagination);

// useProviders использует React Query:
useQuery({
  queryKey: ['providers', filters, pagination],
  queryFn: () => getProviders({ ...filters, ...pagination })
});
```

#### 2. Real-time обновления
```typescript
const { isConnected, lastUpdate } = useWebSocket();

// useWebSocket:
// 1. Подключается к ws://localhost:8000/ws/updates
// 2. Слушает сообщения
// 3. При получении "data_updated" → invalidate queries
// 4. React Query автоматически обновляет данные
```

#### 3. Фильтрация и сортировка
- Пользователь меняет фильтры → обновляется `filters` state
- React Query автоматически перезапрашивает данные с новыми фильтрами
- DataGrid использует серверную пагинацию и сортировку

#### 4. Визуализация
- **StatisticsCharts**: Графики по мерчантам, типам аккаунтов, методам оплаты
- **Dashboard**: Общая аналитика с метриками и трендами
- **Recharts**: Библиотека для графиков (BarChart, PieChart, AreaChart)

### Компоненты

#### DataTable (Material-UI DataGrid)
- Серверная пагинация: `paginationMode="server"`
- Серверная сортировка: `sortingMode="server"`
- Виртуализация строк (оптимизация производительности)
- Редактирование ячеек (inline editing)
- Отображение скриншотов (кнопка просмотра)
- Отображение URL (кнопки открытия в новой вкладке)

#### Filters
- Поиск по всем полям
- Выбор мерчанта (Select)
- Выбор типа аккаунта
- Выбор метода оплаты
- Фильтр по домену провайдера
- Кнопка очистки фильтров

#### ExportButtons
- Экспорт в XLSX (прямая ссылка на файл)
- Экспорт в CSV (с фильтрами)
- Экспорт в JSON (скачивание файла)

#### ImportFromSheets
- Ввод GID листа или имени
- Предпросмотр данных перед импортом
- Кнопка импорта
- Отображение результатов (импортировано/пропущено/ошибок)

#### Dashboard
- Карточки метрик (всего провайдеров, новых сегодня, и т.д.)
- График трендов (AreaChart)
- Распределение по типам аккаунтов (BarChart)
- Топ мерчантов (BarChart)
- Топ провайдеров (BarChart)
- Распределение методов оплаты (BarChart)
- Фильтр по периоду (7/30/90/365 дней)

---

## 5. 🔄 Полный цикл работы

### Сценарий 1: Сбор данных парсером

```
1. Запуск парсера:
   python main_parser_playwright.py --merchant 1win

2. Парсер:
   - Логинится на 1win.in
   - Переходит в кассир
   - Находит все провайдеры в E-WALLETS
   - Для каждого провайдера:
     * Кликает → открывает форму
     * Делает скриншот
     * Извлекает URL, домен, название
     * Сохраняет в SQLite: storage.save_provider(...)
     * Экспортирует в XLSX: storage.export_to_xlsx()

3. Результат:
   - providers_data.db обновлена
   - providers_data.xlsx обновлен
   - screenshots/ пополнен скриншотами
```

### Сценарий 2: Просмотр данных в веб-интерфейсе

```
1. Пользователь открывает http://localhost:5173

2. Frontend:
   - Подключается к WebSocket: ws://localhost:8000/ws/updates
   - Запрашивает данные: GET /api/providers?skip=0&limit=50
   - Запрашивает статистику: GET /api/providers/stats/statistics

3. Backend:
   - Читает данные из SQLite через StorageAdapter
   - Применяет фильтры, сортировку, пагинацию
   - Возвращает JSON: {items: [...], total: 100, ...}

4. Frontend:
   - Отображает данные в DataTable
   - Показывает статистику в карточках
   - Рисует графики на основе статистики

5. Real-time обновления:
   - Backend каждые 5 секунд проверяет изменения в БД
   - При изменении отправляет WebSocket сообщение
   - Frontend получает сообщение → обновляет данные автоматически
```

### Сценарий 3: Импорт из Google Sheets

```
1. Пользователь открывает вкладку "Данные"
2. Видит компонент "ImportFromSheets"
3. Вводит GID: 396039446
4. Нажимает "Предпросмотр":
   - Frontend: GET /api/import/google-sheets/preview?gid=396039446
   - Backend: GoogleSheetsImporter.parse_google_sheets_data(gid)
   - Backend: Подключается к Google Sheets API
   - Backend: Читает данные из листа
   - Backend: Парсит и возвращает preview

5. Пользователь видит предпросмотр в диалоге

6. Нажимает "Импортировать":
   - Frontend: POST /api/import/google-sheets?gid=396039446
   - Backend: GoogleSheetsImporter.import_from_sheet(gid)
   - Backend: Парсит данные
   - Backend: Для каждого провайдера:
     * Проверяет дубликат: storage.provider_exists(...)
     * Если нет дубликата: storage.save_provider(...)
   - Backend: Возвращает результат: {imported: 38, skipped: 297, errors: 0}

7. Frontend показывает результат и обновляет страницу
```

### Сценарий 4: Экспорт данных

```
1. Пользователь применяет фильтры (например, merchant=1win)
2. Нажимает "Экспорт → CSV":
   - Frontend: window.open('/api/export/csv?merchant=1win')
   - Backend: Export API читает данные из БД с фильтрами
   - Backend: Генерирует CSV и возвращает файл
   - Браузер скачивает файл
```

### Сценарий 5: Аналитика

```
1. Пользователь переключается на вкладку "Analytics Dashboard"

2. Frontend:
   - Запрашивает: GET /api/analytics/dashboard?days=7
   - Backend: Анализирует все данные из БД
   - Backend: Вычисляет метрики, тренды, распределения
   - Backend: Возвращает JSON с аналитикой

3. Frontend:
   - Отображает карточки метрик (всего, новых, активных)
   - Рисует график трендов (AreaChart)
   - Рисует графики распределений (BarChart)
   - Позволяет менять период (7/30/90/365 дней)
```

---

## 6. 🐳 Deployment (Docker)

### Docker Compose

```
services:
  backend:
    - Порты: 8000:8000
    - Volumes: 
      * providers_data.db → /app/data/providers_data.db
      * storage.py → /app/storage.py
      * screenshots/ → /app/screenshots
      * google_credentials.json → /app/google_credentials.json
    - Environment: DB_PATH, GOOGLE_SHEET_ID, ...
  
  frontend:
    - Порты: 80:80
    - Depends on: backend
    - Environment: VITE_API_URL=http://localhost/api
```

### Запуск

```bash
# Production
docker-compose up -d

# Local (без Docker)
./start_local.sh
```

---

## 7. 🔐 Безопасность

### Авторизация (опционально)
- JWT токены через `python-jose`
- Хеширование паролей через `passlib` (bcrypt)
- Middleware для проверки токенов

### CORS
- Настраивается через `CORS_ORIGINS` в config.py
- По умолчанию разрешены все origins (для разработки)

---

## 8. 📊 Производительность

### Оптимизации

**Backend:**
- Серверная пагинация (не загружает все данные)
- Индексы в SQLite на часто используемых полях
- Кэширование статистики (можно добавить Redis)

**Frontend:**
- React Query кэширует данные
- Виртуализация строк в DataGrid (рендерит только видимые)
- Lazy loading компонентов (можно добавить)

**WebSocket:**
- Проверка изменений каждые 5 секунд (можно настроить)
- Хеширование данных для быстрого сравнения

---

## 9. 🔧 Технологии

**Backend:**
- FastAPI (Python 3.11+)
- SQLite (база данных)
- Playwright (парсер)
- Pydantic (валидация данных)
- SQLAlchemy (опционально, сейчас прямой SQL)
- WebSockets (real-time)
- gspread (Google Sheets)

**Frontend:**
- React 18+
- TypeScript
- Material-UI (компоненты UI)
- React Query (управление данными)
- Recharts (графики)
- Axios (HTTP клиент)
- Vite (сборка)

**Инфраструктура:**
- Docker & Docker Compose
- Nginx (для production, опционально)

---

## 10. 📝 Конфигурация

### Environment Variables

**Backend (.env):**
```
DB_PATH=/app/data/providers_data.db
XLSX_PATH=/app/data/providers_data.xlsx
GOOGLE_SHEET_ID=1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
GOOGLE_CREDENTIALS_PATH=/app/google_credentials.json
SECRET_KEY=your-secret-key
AUTH_ENABLED=false
CORS_ORIGINS=["http://localhost:5173"]
```

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/updates
```

### Конфигурация мерчантов

`merchants_config.py`:
- Креденшиалы для входа
- CSS селекторы для элементов
- Настройки account_type, form_data

---

## 🎯 Итоговая схема потока данных

```
┌─────────────────────────────────────────────────────────────┐
│                      ПАРСЕР (Playwright)                     │
│  → Логин → Кассир → E-WALLETS → Провайдеры → Скриншоты      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    БАЗА ДАННЫХ (SQLite)                      │
│         providers_data.db + providers_data.xlsx              │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  BACKEND API    │     │  GOOGLE SHEETS  │
│   (FastAPI)     │◄────┤   (Импорт)      │
│                 │     └─────────────────┘
│ - REST API      │
│ - WebSocket     │
│ - Analytics     │
└────────┬────────┘
         │
         │ HTTP/WebSocket
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React)                           │
│  Таблица → Фильтры → Графики → Dashboard → Импорт/Экспорт   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      ПОЛЬЗОВАТЕЛЬ                            │
│          Просматривает, фильтрует, экспортирует              │
└─────────────────────────────────────────────────────────────┘
```

---

**Это полное описание работы сервиса!** 🎉

Сервис представляет собой комплексную систему для сбора, хранения, анализа и визуализации данных о платежных провайдерах гемблинговых сайтов с современным веб-интерфейсом и real-time обновлениями.
