# 🚀 Быстрый старт веб-сервиса

## Вариант A: Streamlit (самый быстрый - 10 минут)

### Установка

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser
pip install streamlit pandas plotly
```

### Создание файла

Создайте файл `web_service_streamlit.py` (см. ARCHITECTURE.md, Вариант 3)

### Запуск

```bash
streamlit run web_service_streamlit.py
```

Откройте http://localhost:8501

---

## Вариант B: React + FastAPI (рекомендуемый для production)

### 1. Настройка Backend (FastAPI)

```bash
# Создайте директорию
mkdir -p web_service/backend/app

# Установите зависимости
cd web_service/backend
pip install fastapi uvicorn python-multipart sqlalchemy pydantic
```

### 2. Создайте базовый FastAPI сервер

Файл: `web_service/backend/app/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional, List
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from storage import Storage

app = FastAPI(title="Providers API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = Storage()

@app.get("/")
def read_root():
    return {"message": "Providers API", "version": "1.0.0"}

@app.get("/api/providers")
def get_providers(
    merchant: Optional[str] = None,
    provider_domain: Optional[str] = None,
    account_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Получить список провайдеров"""
    providers = storage.get_all_providers(merchant=merchant)
    
    # Фильтры
    if provider_domain:
        providers = [p for p in providers if provider_domain.lower() in p.get('provider_domain', '').lower()]
    if account_type:
        providers = [p for p in providers if p.get('account_type') == account_type]
    
    total = len(providers)
    providers = providers[skip:skip+limit]
    
    return {
        "items": providers,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@app.get("/api/export/xlsx")
def export_xlsx():
    """Экспорт в XLSX"""
    storage.export_to_xlsx()
    return FileResponse(
        "providers_data.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="providers_data.xlsx"
    )
```

### 3. Запуск Backend

```bash
cd web_service/backend
uvicorn app.main:app --reload --port 8000
```

API будет доступен на http://localhost:8000
Документация: http://localhost:8000/docs

### 4. Настройка Frontend (React)

```bash
# Создайте React приложение
cd web_service
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Установите зависимости для таблицы
npm install @mui/x-data-grid @mui/material @emotion/react @emotion/styled
npm install @tanstack/react-query axios
```

### 5. Создайте базовый компонент таблицы

Файл: `web_service/frontend/src/App.tsx`

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';

interface Provider {
  id: number;
  merchant: string;
  merchant_domain: string;
  provider_domain: string;
  provider_name: string;
  account_type: string;
  payment_method: string;
  timestamp_utc: string;
}

function App() {
  const [pagination, setPagination] = useState({ page: 0, pageSize: 50 });

  const { data, isLoading } = useQuery({
    queryKey: ['providers', pagination],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/providers`, {
        params: {
          skip: pagination.page * pagination.pageSize,
          limit: pagination.pageSize,
        },
      });
      return response.data;
    },
  });

  const columns: GridColDef[] = [
    { field: 'merchant', headerName: 'Merchant', width: 150 },
    { field: 'merchant_domain', headerName: 'Merchant Domain', width: 200 },
    { field: 'provider_domain', headerName: 'Provider Domain', width: 250 },
    { field: 'provider_name', headerName: 'Provider Name', width: 200 },
    { field: 'account_type', headerName: 'Account Type', width: 150 },
    { field: 'payment_method', headerName: 'Payment Method', width: 150 },
    { field: 'timestamp_utc', headerName: 'Timestamp', width: 200 },
  ];

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <h1>Providers Dashboard</h1>
      <DataGrid
        rows={data?.items || []}
        columns={columns}
        loading={isLoading}
        paginationMode="server"
        rowCount={data?.total || 0}
        page={pagination.page}
        pageSize={pagination.pageSize}
        onPaginationModelChange={(model) =>
          setPagination({ page: model.page, pageSize: model.pageSize })
        }
        checkboxSelection
        disableRowSelectionOnClick
      />
    </div>
  );
}

export default App;
```

### 6. Запуск Frontend

```bash
cd web_service/frontend
npm run dev
```

Frontend будет доступен на http://localhost:5173

---

## Вариант C: Django + HTMX (быстрый старт)

### 1. Создание Django проекта

```bash
pip install django django-cors-headers
django-admin startproject web_service_django
cd web_service_django
python manage.py startapp providers
```

### 2. Настройка settings.py

Добавьте в `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'providers',
    'corsheaders',
]
```

Добавьте middleware:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]
```

CORS настройки:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### 3. Создайте view

Файл: `providers/views.py`

```python
from django.shortcuts import render
from django.http import JsonResponse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from storage import Storage

storage = Storage()

def providers_table(request):
    providers = storage.get_all_providers()
    return render(request, 'providers/table.html', {'providers': providers})
```

### 4. Создайте template

Файл: `providers/templates/providers/table.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Providers Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
</head>
<body>
    <h1>Providers Dashboard</h1>
    <table id="providers-table" class="display">
        <thead>
            <tr>
                <th>Merchant</th>
                <th>Merchant Domain</th>
                <th>Provider Domain</th>
                <th>Provider Name</th>
                <th>Account Type</th>
                <th>Payment Method</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
            {% for provider in providers %}
            <tr>
                <td>{{ provider.merchant }}</td>
                <td>{{ provider.merchant_domain }}</td>
                <td>{{ provider.provider_domain }}</td>
                <td>{{ provider.provider_name }}</td>
                <td>{{ provider.account_type }}</td>
                <td>{{ provider.payment_method }}</td>
                <td>{{ provider.timestamp_utc }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <script>
        $(document).ready(function() {
            $('#providers-table').DataTable({
                pageLength: 50,
                order: [[6, 'desc']]
            });
        });
    </script>
</body>
</html>
```

### 5. Настройка URLs

Файл: `providers/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.providers_table, name='providers_table'),
]
```

Добавьте в основной `urls.py`:
```python
urlpatterns = [
    ...
    path('providers/', include('providers.urls')),
]
```

### 6. Запуск

```bash
python manage.py runserver
```

Откройте http://localhost:8000/providers/

---

## 📋 Checklist для начала работы

- [ ] Выбрать вариант архитектуры
- [ ] Установить зависимости
- [ ] Настроить окружение разработки
- [ ] Создать базовую структуру проекта
- [ ] Настроить интеграцию с существующим Storage
- [ ] Создать первый endpoint/view
- [ ] Протестировать загрузку данных
- [ ] Добавить базовую таблицу
- [ ] Добавить фильтры
- [ ] Добавить экспорт

---

## 🔗 Полезные ссылки

- **FastAPI**: https://fastapi.tiangolo.com/
- **React Query**: https://tanstack.com/query/latest
- **Material-UI DataGrid**: https://mui.com/x/react-data-grid/
- **Streamlit**: https://streamlit.io/
- **Django**: https://www.djangoproject.com/
- **HTMX**: https://htmx.org/

---

## 💡 Следующие шаги после базовой реализации

1. Добавить фильтрацию и поиск
2. Добавить просмотр скриншотов
3. Реализовать редактирование данных
4. Добавить экспорт в различные форматы
5. Настроить real-time обновления (WebSocket)
6. Добавить авторизацию (если нужно)
7. Оптимизировать производительность
8. Добавить тесты
9. Настроить CI/CD
10. Подготовить к production деплою
