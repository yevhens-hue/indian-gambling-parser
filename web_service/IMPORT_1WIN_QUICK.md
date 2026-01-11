# ⚡ Быстрый импорт данных 1win IN из Google Sheets

## 🎯 Что добавлено

✅ **Конфигурация для 1win** - добавлена в `merchants_config.py`  
✅ **API для импорта** - `/api/import/google-sheets`  
✅ **Компонент в UI** - блок импорта в веб-сервисе  
✅ **Парсинг данных** - автоматическое извлечение провайдеров из таблицы  

---

## 🚀 Как использовать

### Через веб-интерфейс (самый простой способ)

1. Откройте http://localhost:5173
2. Найдите блок **"Импорт данных из Google Sheets"** (выше фильтров)
3. Убедитесь, что GID = `396039446` (по умолчанию)
4. Нажмите **"Предпросмотр"** - увидите первые 10 записей
5. Если всё правильно - нажмите **"Импортировать"**
6. Данные автоматически появятся в таблице

### Через API

**Предпросмотр:**
```bash
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=10"
```

**Импорт:**
```bash
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

---

## 📊 Структура данных

Из таблицы будут извлечены:

- **Merchant**: `1win`
- **Merchant Domain**: `1win.com`
- **Account Type**: `FTD` или `STD` (из колонки Account)
- **Provider Domain**: Извлекается из URL или UPI QR кода
- **Provider Name**: Из колонки Bank или Method
- **Payment Method**: `UPI`, `Bank Transfer`, `Wallet`
- **URLs**: Из колонки Links
- **Screenshots**: Google Drive ссылки из колонки Screenshot

---

## ✅ Примеры провайдеров из таблицы

Будут импортированы провайдеры:
- `okbizaxis` (8750270451@okbizaxis)
- `cai-pay.net` 
- `gopay-wallet.com`
- `unicapspay.com`
- `inops.net`
- `indianbnk` (8438925841@indianbnk)
- `hoyorswallet.com`
- `t-payment.net`
- И другие...

---

## ⚙️ Настройка

### Убедитесь, что настроен Google Sheets API:

1. Файл `google_credentials.json` существует
2. Service Account имеет доступ к таблице
3. Google Sheet ID правильный (по умолчанию уже настроен)

**Если не настроено:**
```bash
# См. GOOGLE_SHEETS_SETUP.md для инструкций
cat GOOGLE_SHEETS_SETUP.md
```

---

## 🎯 GID для разных листов

- **1win IN (Scraper PY)**: `396039446`
- **1win AR**: `1910286069` (если нужно добавить)

Для получения GID из URL:
`https://docs.google.com/spreadsheets/d/.../edit?gid=396039446#gid=396039446`
                                                         ^^^^^^^^^
                                                         Это GID

---

## ✨ После импорта

Данные будут:
- ✅ Сохранены в БД (`providers_data.db`)
- ✅ Доступны в веб-сервисе
- ✅ Отображаться в таблице
- ✅ Включаться в статистику
- ✅ Обновляться через WebSocket (если включен)

---

**Готово! Попробуйте импорт через веб-интерфейс или API! 🚀**
