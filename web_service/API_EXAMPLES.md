# 📚 Примеры использования API

**Дата:** 2026-01-11  
**Версия API:** 1.1.0

---

## 🚀 Быстрый старт

### Base URL

```
http://localhost:8000
```

### API Prefix

```
/api
```

---

## 📋 Endpoints

### 1. Получить список провайдеров

**Endpoint:** `GET /api/providers`

**Параметры:**
- `merchant` (optional) - Фильтр по мерчанту
- `provider_domain` (optional) - Фильтр по домену провайдера
- `account_type` (optional) - Фильтр по типу аккаунта
- `payment_method` (optional) - Фильтр по методу оплаты
- `search` (optional) - Текстовый поиск
- `skip` (optional, default: 0) - Пропустить N записей
- `limit` (optional, default: 50) - Максимум записей
- `sort_by` (optional, default: timestamp_utc) - Поле для сортировки
- `sort_order` (optional, default: desc) - Порядок сортировки (asc/desc)

**Пример запроса:**
```bash
curl "http://localhost:8000/api/providers?merchant=1xbet&limit=10&sort_by=timestamp_utc&sort_order=desc"
```

**Пример ответа:**
```json
{
  "items": [
    {
      "id": 1,
      "merchant": "1xbet",
      "merchant_domain": "indian.1xbet.com",
      "provider_domain": "paytm.com",
      "provider_name": "Paytm",
      "account_type": "player",
      "payment_method": "e-wallet",
      "timestamp_utc": "2026-01-11T12:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

---

### 2. Получить провайдера по ID

**Endpoint:** `GET /api/providers/{id}`

**Пример запроса:**
```bash
curl "http://localhost:8000/api/providers/1"
```

**Пример ответа:**
```json
{
  "id": 1,
  "merchant": "1xbet",
  "provider_domain": "paytm.com",
  "provider_name": "Paytm",
  "account_type": "player",
  "payment_method": "e-wallet"
}
```

---

### 3. Обновить провайдера

**Endpoint:** `PUT /api/providers/{id}`

**Пример запроса:**
```bash
curl -X PUT "http://localhost:8000/api/providers/1" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "Paytm Updated",
    "payment_method": "upi"
  }'
```

**Пример ответа:**
```json
{
  "success": true,
  "provider": {
    "id": 1,
    "provider_name": "Paytm Updated",
    "payment_method": "upi"
  }
}
```

---

### 4. API v1 - Получить провайдеров

**Endpoint:** `GET /api/v1/providers`

**Пример запроса:**
```bash
curl "http://localhost:8000/api/v1/providers?limit=5"
```

**Пример ответа:**
```json
{
  "total": 100,
  "items": [...],
  "skip": 0,
  "limit": 5,
  "version": "v1"
}
```

---

### 5. Экспорт данных

**XLSX:**
```bash
curl "http://localhost:8000/api/export/xlsx" -o providers.xlsx
```

**CSV:**
```bash
curl "http://localhost:8000/api/export/csv" -o providers.csv
```

**JSON:**
```bash
curl "http://localhost:8000/api/export/json" -o providers.json
```

**PDF:**
```bash
curl "http://localhost:8000/api/export/pdf" -o providers.pdf
```

**Форматированный Excel:**
```bash
curl "http://localhost:8000/api/export/xlsx?formatted=true" -o providers_formatted.xlsx
```

---

### 6. Статистика

**Endpoint:** `GET /api/providers/stats/statistics`

**Пример запроса:**
```bash
curl "http://localhost:8000/api/providers/stats/statistics"
```

**Пример ответа:**
```json
{
  "total": 100,
  "merchants": {
    "1xbet": 50,
    "1win": 30,
    "olymptrade": 20
  },
  "account_types": {
    "player": 100
  },
  "payment_methods": {
    "e-wallet": 60,
    "upi": 40
  }
}
```

---

### 7. Health Check

**Endpoint:** `GET /health`

**Пример запроса:**
```bash
curl "http://localhost:8000/health"
```

**Пример ответа:**
```json
{
  "status": "ok",
  "checks": {
    "database": {
      "status": "ok",
      "message": "Connected, 100 providers"
    },
    "cache": {
      "status": "ok",
      "enabled": true
    }
  },
  "timestamp": "2026-01-11T12:00:00Z"
}
```

---

### 8. Metrics (Prometheus)

**Endpoint:** `GET /metrics`

**Пример запроса:**
```bash
curl "http://localhost:8000/metrics"
```

---

## 🔐 Аутентификация

Если `AUTH_ENABLED=true`:

**Получить токен:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**Использовать токен:**
```bash
curl "http://localhost:8000/api/providers" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📝 Примеры на Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Получить провайдеров
response = requests.get(f"{BASE_URL}/providers", params={
    "merchant": "1xbet",
    "limit": 10
})
providers = response.json()

# Обновить провайдера
response = requests.put(
    f"{BASE_URL}/providers/1",
    json={"provider_name": "Updated Name"}
)
result = response.json()

# Экспорт в XLSX
response = requests.get(f"{BASE_URL}/export/xlsx")
with open("providers.xlsx", "wb") as f:
    f.write(response.content)
```

---

## 📝 Примеры на JavaScript

```javascript
const BASE_URL = "http://localhost:8000/api";

// Получить провайдеров
const response = await fetch(`${BASE_URL}/providers?merchant=1xbet&limit=10`);
const data = await response.json();

// Обновить провайдера
const updateResponse = await fetch(`${BASE_URL}/providers/1`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ provider_name: "Updated Name" })
});
const result = await updateResponse.json();
```

---

## 🔗 WebSocket

**Подключение:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("New provider:", data);
};
```

---

## 📚 Дополнительная документация

- **OpenAPI Schema:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Versioning:** `API_VERSIONING.md`

---

**Дата:** 2026-01-11  
**Версия:** 1.1.0
