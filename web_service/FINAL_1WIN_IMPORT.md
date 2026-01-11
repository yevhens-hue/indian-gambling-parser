# ✅ Импорт данных 1win IN - Реализовано!

## 🎉 Что сделано

### 1. ✅ Конфигурация для 1win
- Добавлена в `merchants_config.py`
- Поддержка доменов: `1win.com`, `1win.in`, `www.1win.com`
- Настройки для парсинга: селекторы, account_type (FTD/STD), UPI данные

### 2. ✅ Сервис импорта из Google Sheets
- Файл: `backend/app/services/google_sheets_importer.py`
- Парсинг данных из таблицы по GID или названию листа
- Извлечение провайдеров из URL и UPI QR кодов
- Нормализация доменов

### 3. ✅ API Endpoints
- `GET /api/import/google-sheets/preview` - предпросмотр данных
- `POST /api/import/google-sheets` - импорт данных в БД

### 4. ✅ UI Компонент
- Компонент `ImportFromSheets` в веб-сервисе
- Блок импорта выше фильтров
- Предпросмотр и импорт с одного интерфейса

---

## 🚀 Как использовать (3 способа)

### Способ 1: Веб-интерфейс ⭐ (самый простой)

1. Откройте http://localhost:5173
2. Найдите блок **"Импорт данных из Google Sheets"**
3. Убедитесь, что GID = `396039446` (по умолчанию)
4. Нажмите **"Предпросмотр"** (опционально)
5. Нажмите **"Импортировать"**
6. Готово! Данные появятся в таблице

### Способ 2: API

```bash
# Предпросмотр
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=10"

# Импорт
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Способ 3: Swagger UI

1. Откройте http://localhost:8000/docs
2. Найдите `POST /api/import/google-sheets`
3. Укажите параметр: `gid` = `396039446`
4. Нажмите "Try it out" → "Execute"

---

## 📊 Данные, которые будут импортированы

Из таблицы **"Scraper (PY)"** (gid=396039446) будут импортированы:

### Провайдеры:
- ✅ `okbizaxis` (8750270451@okbizaxis) - UPI
- ✅ `cai-pay.net` - PayTm провайдеры
- ✅ `gopay-wallet.com` - Gpay/Wallet
- ✅ `unicapspay.com` - UPI провайдеры
- ✅ `inops.net` - UPI провайдеры
- ✅ `indianbnk` (8438925841@indianbnk) - UPI банки
- ✅ `hoyorswallet.com` - Wallet
- ✅ `t-payment.net` - Gpay
- ✅ `bpglobalfav.live` - PayTm
- ✅ И другие провайдеры из таблицы...

### Account Types:
- `FTD` - First Time Deposit
- `STD` - Standard Deposit

### Payment Methods:
- `UPI` - UPI платежи (PhonePe, GPay, PayTm, UPI)
- `Bank Transfer` - Банковские переводы
- `Wallet` - Электронные кошельки

---

## ⚙️ Настройка перед использованием

### 1. Google Sheets API

Убедитесь, что настроен доступ:

```bash
# Проверьте наличие файла
ls google_credentials.json

# Если нет - создайте (см. GOOGLE_SHEETS_SETUP.md)
```

### 2. Перезапустите backend

```bash
cd web_service/backend
python3 start.py
```

### 3. Обновите frontend (если нужно)

```bash
cd web_service/frontend
npm run dev
```

---

## 📋 Структура импортированных данных

Каждая запись будет содержать:

```json
{
  "merchant": "1win",
  "merchant_domain": "1win.com",
  "account_type": "FTD" или "STD",
  "provider_domain": "okbizaxis" (извлечен из URL или QR),
  "provider_name": "okbizaxis" (из колонки Bank),
  "provider_entry_url": "https://1win.com/...",
  "final_url": "https://cai-pay.net/...",
  "cashier_url": "https://1win.com/",
  "screenshot_path": "https://drive.google.com/...",
  "detected_in": "google_sheets_import",
  "payment_method": "UPI",
  "is_iframe": false,
  "requires_otp": false,
  "blocked_by_geo": false,
  "captcha_present": false,
  "timestamp_utc": "2026-01-10T..."
}
```

---

## 🔍 Как найти GID листа

Из URL таблицы:
```
https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE/edit?gid=396039446#gid=396039446
                                                                              ^^^^^^^^^
                                                                              Это GID
```

---

## ✨ После импорта

После успешного импорта данные:

1. ✅ **Сохранены в БД** - `providers_data.db`
2. ✅ **Отображаются в таблице** - автоматически
3. ✅ **В статистике** - учитываются в графиках
4. ✅ **В фильтрах** - можно фильтровать по `merchant=1win`
5. ✅ **WebSocket** - обновления отправляются (если включен)

---

## 🎯 Быстрый тест

### Проверка работы API:

```bash
# 1. Предпросмотр (должен показать первые 10 записей)
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"

# 2. Импорт (импортирует все записи)
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Проверка в веб-сервисе:

1. Откройте http://localhost:5173
2. Найдите блок импорта
3. Нажмите "Предпросмотр" - должно показать данные
4. Нажмите "Импортировать" - данные появятся в таблице

---

## 📚 Документация

- **IMPORT_1WIN.md** - Полное руководство
- **IMPORT_1WIN_QUICK.md** - Краткая инструкция
- **USAGE_1WIN_IMPORT.md** - Инструкции по использованию
- **GOOGLE_SHEETS_SETUP.md** - Настройка Google Sheets API

---

## 🎉 Готово!

**Импорт данных 1win IN полностью реализован!**

Попробуйте импорт через веб-интерфейс или API - данные автоматически появятся в вашей таблице! 🚀
