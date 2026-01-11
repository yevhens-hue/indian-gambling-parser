# 📥 Импорт данных 1win IN из Google Sheets

## ✅ Реализовано

1. ✅ Добавлена конфигурация для 1win в `merchants_config.py`
2. ✅ Создан сервис для импорта данных из Google Sheets
3. ✅ API endpoints для импорта данных
4. ✅ Парсинг данных из таблицы 1win (gid=396039446)

---

## 🚀 Как использовать

### Вариант 1: Через API (рекомендуется)

**Предпросмотр данных перед импортом:**
```bash
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=10"
```

**Импорт данных:**
```bash
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Вариант 2: Через Swagger UI

1. Откройте http://localhost:8000/docs
2. Найдите endpoint `POST /api/import/google-sheets`
3. Укажите параметр `gid=396039446`
4. Нажмите Execute

### Вариант 3: Через Python скрипт

```python
from app.services.google_sheets_importer import GoogleSheetsImporter

importer = GoogleSheetsImporter()
result = importer.import_from_sheet(gid="396039446")
print(result)
```

---

## 📊 Структура данных из Google Sheets

Таблица содержит следующие колонки:
- **Method** - Метод оплаты (UPI, PhonePe, PayTm, GPay, Bank transfer)
- **Type** - Тип (Parser)
- **Account** - Тип аккаунта (FTD, STD)
- **Date** - Дата
- **Links** - URL провайдеров
- **Screenshot** - Ссылка на Google Drive скриншот
- **QR** - UPI QR код
- **Status** - Статус (Success)
- **Bank** - Название банка/провайдера
- **UPI ID** - UPI идентификатор

---

## 🔧 Как работает импорт

1. **Чтение данных из Google Sheets**
   - Использует gid из URL для определения листа
   - Читает все строки (кроме заголовков)

2. **Парсинг данных**
   - Извлекает провайдеров из колонки Links
   - Извлекает домены из URL
   - Определяет payment_method из Method
   - Извлекает данные из QR кодов (UPI)

3. **Нормализация доменов**
   - Использует tldextract для нормализации
   - Преобразует в eTLD+1 формат

4. **Сохранение в БД**
   - Проверяет дубликаты (merchant_domain + provider_domain + account_type)
   - Сохраняет только новые записи
   - Возвращает статистику (импортировано, пропущено, ошибки)

---

## 📋 Примеры данных

Из таблицы будут извлечены провайдеры:
- `okbizaxis` (из UPI ID: 8750270451@okbizaxis)
- `cai-pay.net` (из URL: https://cai-pay.net/mobile/...)
- `gopay-wallet.com` (из URL: https://pay.gopay-wallet.com/...)
- `unicapspay.com` (из URL: https://checkouts.unicapspay.com/...)
- `inops.net` (из URL: https://app.inops.net/payment/...)
- И другие провайдеры из таблицы

---

## ⚙️ Настройка

### Google Sheets credentials

Убедитесь, что файл `google_credentials.json` существует и настроен:
- См. `GOOGLE_SHEETS_SETUP.md` для инструкций
- Service Account должен иметь доступ к таблице

### Google Sheet ID

По умолчанию используется ID из config:
- `GOOGLE_SHEET_ID=1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE`

### GID листа

Для листа "Scraper (PY)":
- GID из URL: `396039446`
- URL: `https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE/edit?gid=396039446`

---

## 🧪 Тестирование

### Предпросмотр (без импорта)
```bash
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=5"
```

### Импорт данных
```bash
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

### Ответ:
```json
{
  "status": "success",
  "message": "Импортировано 50 провайдеров",
  "imported": 50,
  "skipped": 10,
  "errors": 0,
  "total": 60
}
```

---

## 🔄 Синхронизация

Данные из Google Sheets будут:
- ✅ Импортированы в SQLite БД
- ✅ Доступны в веб-сервисе
- ✅ Отображаться в таблице с фильтрами
- ✅ Включаться в статистику и графики
- ✅ Обновляться через WebSocket (если включен)

---

## 📝 Примечания

- **Дубликаты**: Автоматически пропускаются (проверка по merchant_domain + provider_domain + account_type)
- **Account Type**: Извлекается из колонки Account (FTD или STD)
- **Provider Domain**: Извлекается из URL или UPI QR кода
- **Screenshots**: Хранятся как Google Drive URL (не скачиваются)

---

## 🐛 Troubleshooting

### Ошибка: "Файл credentials не найден"
**Решение:** Создайте Service Account и скачайте JSON ключ (см. GOOGLE_SHEETS_SETUP.md)

### Ошибка: "Google Sheet ID не указан"
**Решение:** Проверьте переменную окружения `GOOGLE_SHEET_ID` или установите в `config.py`

### Ошибка: "Лист не найден"
**Решение:** Проверьте правильность gid в URL таблицы

### Нет данных после импорта
**Решение:** 
1. Проверьте предпросмотр: `/api/import/google-sheets/preview?gid=396039446`
2. Убедитесь, что в таблице есть данные для 1win
3. Проверьте логи импорта

---

**Готово к использованию! 🎉**
