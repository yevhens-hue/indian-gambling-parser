# 🏗️ Архитектура веб-сервиса для управления данными провайдеров

Документ описывает несколько вариантов архитектуры для создания веб-сервиса, аналогичного Google Sheets, для отображения и управления данными парсера провайдеров.

## 📋 Требования к функциональности

### Основной функционал
1. **Табличное отображение данных** - как в Google Sheets
2. **Фильтрация и сортировка** - по merchant, provider, account_type, payment_method
3. **Поиск** - полнотекстовый поиск по всем полям
4. **Редактирование данных** - inline editing в ячейках
5. **Просмотр скриншотов** - отображение screenshots при клике
6. **Экспорт данных** - XLSX, CSV, JSON
7. **Множественные вкладки (табы)** - как в Google Sheets (gid параметры)
8. **Real-time обновления** - автоматическое обновление при новых данных от парсера
9. **История изменений** - логирование всех изменений
10. **Фильтры и группировка** - продвинутые возможности фильтрации

### Технические требования
- Поддержка большого объема данных (10k+ строк)
- Быстрая загрузка и отклик интерфейса
- Responsive дизайн (работа на мобильных устройствах)
- Безопасность (авторизация, валидация данных)

---

## 🎯 Вариант 1: React + FastAPI + SQLite/PostgreSQL (Рекомендуемый)

### Архитектура

```
┌─────────────────┐
│   React SPA     │  Frontend (TypeScript, Material-UI или Ant Design)
│   (localhost:3000)│
└────────┬────────┘
         │ REST API / WebSocket
┌────────▼────────┐
│   FastAPI       │  Backend (Python 3.10+)
│   (localhost:8000)│
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLite/PostgreSQL│  База данных
│  (providers_data.db)│
└─────────────────┘
```

### Структура проекта

```
indian_gambling_parser/
├── frontend/                    # React приложение
│   ├── src/
│   │   ├── components/
│   │   │   ├── DataTable/      # Основной компонент таблицы
│   │   │   ├── Filters/        # Компоненты фильтрации
│   │   │   ├── ScreenshotViewer/ # Просмотр скриншотов
│   │   │   └── ExportButtons/  # Кнопки экспорта
│   │   ├── services/
│   │   │   └── api.ts          # API клиент
│   │   ├── hooks/
│   │   │   └── useProviders.ts # Custom hooks для данных
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts          # или create-react-app
│
├── backend/                     # FastAPI сервер
│   ├── app/
│   │   ├── main.py             # Точка входа FastAPI
│   │   ├── api/
│   │   │   ├── providers.py    # CRUD endpoints для providers
│   │   │   ├── export.py       # Экспорт endpoints
│   │   │   └── websocket.py    # WebSocket для real-time
│   │   ├── models/
│   │   │   └── provider.py     # Pydantic models
│   │   ├── services/
│   │   │   ├── storage.py      # Адаптер для существующего Storage
│   │   │   └── export_service.py
│   │   └── database.py         # SQLAlchemy setup
│   ├── requirements.txt
│   └── Dockerfile
│
└── shared/                      # Общие типы (опционально)
    └── types.ts
```

### Технологический стек

**Frontend:**
- React 18+ (TypeScript)
- Material-UI / Ant Design / AG-Grid (для таблиц)
- React Query / SWR (для кеширования данных)
- Socket.io-client (для real-time обновлений)
- React Router (для навигации между табами)

**Backend:**
- FastAPI (Python)
- SQLAlchemy (ORM)
- Pydantic (валидация данных)
- WebSockets (для real-time)
- Celery (опционально, для фоновых задач)

### Пример кода

#### Backend (FastAPI)

```python
# backend/app/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import asyncio

app = FastAPI()

# CORS для React приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к существующему Storage
from storage import Storage
storage = Storage()

@app.get("/api/providers")
async def get_providers(
    merchant: str = None,
    provider_domain: str = None,
    account_type: str = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "timestamp_utc",
    sort_order: str = "desc"
):
    """Получить список провайдеров с пагинацией и фильтрами"""
    providers = storage.get_all_providers(merchant=merchant)
    
    # Применяем фильтры
    if provider_domain:
        providers = [p for p in providers if provider_domain.lower() in p.get('provider_domain', '').lower()]
    if account_type:
        providers = [p for p in providers if p.get('account_type') == account_type]
    
    # Сортировка
    reverse = sort_order == "desc"
    providers.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
    
    # Пагинация
    total = len(providers)
    providers = providers[skip:skip+limit]
    
    return {
        "items": providers,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@app.put("/api/providers/{provider_id}")
async def update_provider(provider_id: int, data: dict):
    """Обновить данные провайдера"""
    # Реализация обновления через Storage
    pass

@app.get("/api/export/xlsx")
async def export_xlsx():
    """Экспорт в XLSX"""
    storage.export_to_xlsx()
    return FileResponse("providers_data.xlsx")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await websocket.accept()
    while True:
        # Проверяем изменения в БД
        await asyncio.sleep(5)
        await websocket.send_json({"type": "update_available"})
```

#### Frontend (React)

```typescript
// frontend/src/components/DataTable/DataTable.tsx
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataGrid, GridColDef } from '@mui/x-data-grid';

const DataTable: React.FC = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({ page: 0, pageSize: 50 });

  const { data, isLoading } = useQuery({
    queryKey: ['providers', filters, pagination],
    queryFn: () => fetchProviders(filters, pagination),
  });

  const updateMutation = useMutation({
    mutationFn: updateProvider,
    onSuccess: () => {
      queryClient.invalidateQueries(['providers']);
    },
  });

  const columns: GridColDef[] = [
    { field: 'merchant', headerName: 'Merchant', editable: true },
    { field: 'provider_domain', headerName: 'Provider Domain', width: 250 },
    { field: 'provider_name', headerName: 'Provider Name', editable: true },
    { field: 'account_type', headerName: 'Account Type', width: 150 },
    { field: 'payment_method', headerName: 'Payment Method' },
    { 
      field: 'screenshot_path', 
      headerName: 'Screenshot',
      renderCell: (params) => (
        <img 
          src={`/api/screenshots/${params.value}`} 
          alt="screenshot" 
          style={{ width: 50, cursor: 'pointer' }}
          onClick={() => openScreenshotModal(params.value)}
        />
      )
    },
    { field: 'timestamp_utc', headerName: 'Timestamp', width: 180 },
  ];

  return (
    <DataGrid
      rows={data?.items || []}
      columns={columns}
      loading={isLoading}
      pageSize={pagination.pageSize}
      rowsPerPageOptions={[25, 50, 100]}
      onCellEditCommit={(params) => updateMutation.mutate({
        id: params.id,
        [params.field]: params.value,
      })}
    />
  );
};
```

### Преимущества
✅ Разделение frontend/backend  
✅ Современный стек (React, FastAPI)  
✅ Типобезопасность (TypeScript, Pydantic)  
✅ Real-time обновления через WebSocket  
✅ Легко расширяется  
✅ Хорошая производительность  

### Недостатки
❌ Требует знания двух языков (Python + TypeScript)  
❌ Более сложная настройка (два сервера)  
❌ Больше зависимостей  

### Оценка трудозатрат
- Frontend: 40-60 часов
- Backend: 20-30 часов
- Интеграция: 10-15 часов
- **Итого: 70-105 часов**

---

## 🎯 Вариант 2: Django + HTMX + Alpine.js (Минималистичный)

### Архитектура

```
┌─────────────────┐
│   Django + HTMX │  Monolith приложение
│   (localhost:8000)│
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLite/PostgreSQL│  База данных
│  (providers_data.db)│
└─────────────────┘
```

### Структура проекта

```
indian_gambling_parser/
├── web_service/                 # Django приложение
│   ├── manage.py
│   ├── web_service/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── providers/
│   │   ├── models.py            # Django models (адаптер к Storage)
│   │   ├── views.py             # HTMX views
│   │   ├── urls.py
│   │   └── templates/
│   │       └── providers/
│   │           ├── table.html   # Основная таблица
│   │           └── filters.html # Фильтры
│   └── static/
│       └── js/
│           └── table.js         # Alpine.js логика
```

### Технологический стек

**Backend:**
- Django 4.x
- Django REST Framework (опционально, для API)
- Django Channels (для WebSocket, опционально)

**Frontend:**
- HTMX (для динамических обновлений без JS)
- Alpine.js (для интерактивности)
- Tailwind CSS (для стилей)
- DataTables.js или Handsontable (для таблиц)

### Пример кода

#### Django View

```python
# web_service/providers/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from storage import Storage

storage = Storage()

def providers_table(request):
    """Главная страница с таблицей"""
    providers = storage.get_all_providers()
    return render(request, 'providers/table.html', {'providers': providers})

@require_http_methods(["GET"])
def providers_api(request):
    """API endpoint для HTMX запросов"""
    merchant = request.GET.get('merchant')
    providers = storage.get_all_providers(merchant=merchant)
    return render(request, 'providers/table_rows.html', {'providers': providers})

@require_http_methods(["PUT"])
def update_provider(request, provider_id):
    """Обновление провайдера"""
    # Обновление через Storage
    return JsonResponse({'status': 'ok'})
```

#### HTML Template (HTMX)

```html
<!-- web_service/providers/templates/providers/table.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
</head>
<body>
    <div x-data="{ filters: {} }">
        <!-- Фильтры -->
        <div class="filters">
            <input type="text" 
                   placeholder="Merchant" 
                   hx-get="/api/providers"
                   hx-target="#table-body"
                   hx-trigger="input changed delay:500ms"
                   name="merchant">
        </div>

        <!-- Таблица -->
        <table id="providers-table" class="display">
            <thead>
                <tr>
                    <th>Merchant</th>
                    <th>Provider Domain</th>
                    <th>Provider Name</th>
                    <th>Account Type</th>
                    <th>Screenshot</th>
                </tr>
            </thead>
            <tbody id="table-body" hx-get="/api/providers" hx-trigger="load">
                {% include 'providers/table_rows.html' %}
            </tbody>
        </table>
    </div>

    <script>
        $(document).ready(function() {
            $('#providers-table').DataTable({
                pageLength: 50,
                order: [[5, 'desc']] // Сортировка по timestamp
            });
        });
    </script>
</body>
</html>
```

### Преимущества
✅ Один язык (Python)  
✅ Простая архитектура (monolith)  
✅ Быстрая разработка  
✅ Минимальный JavaScript  
✅ Легко деплоить (один сервер)  

### Недостатки
❌ Менее интерактивный UI  
❌ Ограниченные возможности real-time  
❌ Менее современный подход  

### Оценка трудозатрат
- Django setup: 5-10 часов
- Templates и views: 15-20 часов
- Фильтрация и поиск: 10-15 часов
- Интеграция с Storage: 5-10 часов
- **Итого: 35-55 часов**

---

## 🎯 Вариант 3: Streamlit (Прототип / MVP)

### Архитектура

```
┌─────────────────┐
│   Streamlit     │  Python приложение
│   (localhost:8501)│
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLite         │  База данных
│  (providers_data.db)│
└─────────────────┘
```

### Структура проекта

```
indian_gambling_parser/
├── web_service_streamlit.py    # Один файл Streamlit приложения
└── requirements.txt             # Добавить streamlit, pandas, plotly
```

### Технологический стек

- Streamlit (Python)
- Pandas (для работы с данными)
- Plotly (для визуализации)

### Пример кода

```python
# web_service_streamlit.py
import streamlit as st
import pandas as pd
from storage import Storage
from pathlib import Path

st.set_page_config(page_title="Providers Dashboard", layout="wide")

storage = Storage()

# Загрузка данных
@st.cache_data(ttl=60)
def load_providers():
    return storage.get_all_providers()

providers = load_providers()
df = pd.DataFrame(providers)

# Sidebar с фильтрами
st.sidebar.header("Фильтры")
merchant_filter = st.sidebar.selectbox("Merchant", ["All"] + list(df['merchant'].unique()))
account_type_filter = st.sidebar.selectbox("Account Type", ["All"] + list(df['account_type'].dropna().unique()))

# Применение фильтров
filtered_df = df.copy()
if merchant_filter != "All":
    filtered_df = filtered_df[filtered_df['merchant'] == merchant_filter]
if account_type_filter != "All":
    filtered_df = filtered_df[filtered_df['account_type'] == account_type_filter]

# Главная таблица
st.header("Провайдеры")
st.dataframe(
    filtered_df,
    use_container_width=True,
    height=600,
    column_config={
        "screenshot_path": st.column_config.ImageColumn("Screenshot"),
        "timestamp_utc": st.column_config.DatetimeColumn("Timestamp"),
    }
)

# Статистика
col1, col2, col3 = st.columns(3)
col1.metric("Всего провайдеров", len(filtered_df))
col2.metric("Уникальных мерчантов", filtered_df['merchant'].nunique())
col3.metric("Уникальных доменов", filtered_df['provider_domain'].nunique())

# Экспорт
if st.button("Экспорт в XLSX"):
    storage.export_to_xlsx()
    st.success("Экспортировано!")
```

### Преимущества
✅ Очень быстрая разработка (1-2 дня)  
✅ Один файл  
✅ Встроенные виджеты (фильтры, графики)  
✅ Идеален для MVP  
✅ Минимальные зависимости  

### Недостатки
❌ Ограниченная кастомизация UI  
❌ Не подходит для production с большими данными  
❌ Нет real-time обновлений  
❌ Ограниченные возможности редактирования  

### Оценка трудозатрат
- Разработка: 8-12 часов
- Тестирование: 2-4 часа
- **Итого: 10-16 часов**

---

## 🎯 Вариант 4: Flask + React (Гибридный)

### Архитектура

```
┌─────────────────┐
│   React SPA     │  Frontend (отдельный сервер или статика)
│   (localhost:3000)│
└────────┬────────┘
         │ REST API
┌────────▼────────┐
│   Flask         │  Backend (Python)
│   (localhost:5000)│
└────────┬────────┘
         │
┌────────▼────────┐
│  SQLite         │  База данных
└─────────────────┘
```

### Технологический стек

**Backend:**
- Flask + Flask-RESTful
- Flask-CORS
- Flask-SocketIO (для WebSocket)

**Frontend:**
- React (как в варианте 1)

### Преимущества
✅ Проще чем FastAPI (для тех, кто знает Flask)  
✅ Легче миграция с существующего кода  
✅ Много готовых расширений  

### Недостатки
❌ Менее производительный чем FastAPI  
❌ Устаревший подход к сравнению с FastAPI  

### Оценка трудозатрат
- Backend: 25-35 часов
- Frontend: 40-60 часов
- **Итого: 65-95 часов**

---

## 🎯 Вариант 5: Next.js (Full-stack JavaScript)

### Архитектура

```
┌─────────────────┐
│   Next.js       │  Full-stack React приложение
│   (localhost:3000)│  (API Routes + Frontend)
└────────┬────────┘
         │
┌────────▼────────┐
│  Python Service │  Микросервис для работы с Storage
│  (FastAPI/Flask)│  или прямой доступ к SQLite через node-sqlite3
└─────────────────┘
```

### Технологический стек

- Next.js 13+ (App Router)
- TypeScript
- Prisma (ORM) или node-sqlite3
- Tailwind CSS
- shadcn/ui (компоненты)

### Преимущества
✅ Один язык (TypeScript/JavaScript)  
✅ Отличная производительность (SSR/SSG)  
✅ Современный стек  
✅ Хорошая SEO (если нужно)  

### Недостатки
❌ Нужно переписать Storage на Node.js или использовать Python сервис  
❌ Больше сложности с интеграцией существующего кода  

### Оценка трудозатрат
- Next.js setup: 10-15 часов
- API routes: 20-30 часов
- Frontend: 40-50 часов
- Интеграция: 15-20 часов
- **Итого: 85-115 часов**

---

## 📊 Сравнительная таблица вариантов

| Критерий | Вариант 1<br/>(React+FastAPI) | Вариант 2<br/>(Django+HTMX) | Вариант 3<br/>(Streamlit) | Вариант 4<br/>(Flask+React) | Вариант 5<br/>(Next.js) |
|----------|------------------------------|----------------------------|---------------------------|----------------------------|------------------------|
| **Скорость разработки** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Производительность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Гибкость UI** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Простота поддержки** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Real-time** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Интеграция с существующим кодом** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Оценка трудозатрат (часы)** | 70-105 | 35-55 | 10-16 | 65-95 | 85-115 |

---

## 🎯 Рекомендации по выбору

### Для быстрого MVP / Прототипа
**Вариант 3 (Streamlit)** - можно собрать за 1-2 дня

### Для production с минимальными усилиями
**Вариант 2 (Django + HTMX)** - хороший баланс скорости и функциональности

### Для современного production решения
**Вариант 1 (React + FastAPI)** - лучший выбор для долгосрочного проекта

### Для команды, знающей только Python
**Вариант 2 или 3** в зависимости от требований

### Для команды, знающей JavaScript
**Вариант 5 (Next.js)** или **Вариант 1 (React + FastAPI)**

---

## 🚀 План реализации (рекомендуемый - Вариант 1)

### Фаза 1: Подготовка (2-3 дня)
1. Настройка структуры проекта (frontend/backend)
2. Настройка окружения разработки
3. Создание базовых API endpoints
4. Интеграция с существующим Storage

### Фаза 2: Базовый функционал (5-7 дней)
1. Табличное отображение данных
2. Пагинация и сортировка
3. Базовые фильтры
4. Просмотр скриншотов

### Фаза 3: Расширенный функционал (5-7 дней)
1. Редактирование данных
2. Продвинутые фильтры
3. Экспорт (XLSX, CSV, JSON)
4. Поиск

### Фаза 4: Улучшения (3-5 дней)
1. Real-time обновления (WebSocket)
2. История изменений
3. Оптимизация производительности
4. Тестирование

### Фаза 5: Деплой (2-3 дня)
1. Настройка production окружения
2. Docker контейнеризация
3. CI/CD настройка
4. Мониторинг

**Общая оценка: 17-25 дней разработки**

---

## 📁 Структура файлов для реализации (Вариант 1)

Рекомендуемая структура будет создана в следующих файлах:

```
indian_gambling_parser/
├── web_service/                 # Новый модуль веб-сервиса
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py         # FastAPI app
│   │   │   ├── config.py       # Конфигурация
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── providers.py
│   │   │   │   ├── export.py
│   │   │   │   └── websocket.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── provider.py
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── storage_adapter.py
│   │   │       └── export_service.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── frontend/
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── src/
│       │   ├── App.tsx
│       │   ├── main.tsx
│       │   ├── components/
│       │   │   ├── DataTable/
│       │   │   ├── Filters/
│       │   │   ├── ScreenshotViewer/
│       │   │   └── ExportButtons/
│       │   ├── services/
│       │   │   └── api.ts
│       │   └── hooks/
│       │       └── useProviders.ts
│       └── public/
│
└── (существующие файлы парсера)
```

---

## 🔧 Дополнительные соображения

### Множественные вкладки (табы)
Реализация через:
- React Router с разными routes для каждого таба
- Хранение состояния фильтров в URL query параметрах
- Или через отдельные компоненты с переключением

### Real-time обновления
- WebSocket соединение для push-уведомлений о новых данных
- Периодический polling как fallback
- Индикатор "новые данные доступны" с кнопкой обновления

### Производительность
- Виртуализация таблицы (react-window, react-virtualized)
- Server-side пагинация
- Кеширование на frontend (React Query)
- Индексы в БД для быстрых запросов

### Безопасность
- JWT токены для авторизации (опционально)
- Валидация всех входных данных
- Rate limiting на API
- CORS настройки

---

## 📝 Следующие шаги

1. Выберите вариант архитектуры
2. Создайте структуру проекта
3. Настройте окружение разработки
4. Реализуйте базовый функционал
5. Постепенно добавляйте расширенные возможности

Какой вариант вам больше подходит? Могу помочь с началом реализации любого из них.
