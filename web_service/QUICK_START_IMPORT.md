# ⚡ Быстрый старт: Импорт данных 1win IN

## ✅ Готово к использованию!

Импорт данных из Google Sheets настроен и готов к работе. 

**Найдено записей:** 335 провайдеров из таблицы 1win IN

---

## 🚀 Импорт данных (3 способа)

### Способ 1: Веб-интерфейс ⭐ (рекомендуется)

1. **Запустите веб-сервис:**
   ```bash
   # Backend
   cd web_service/backend
   python3 start.py
   
   # Frontend (в другом терминале)
   cd web_service/frontend
   npm run dev
   ```

2. **Откройте:** http://localhost:5173

3. **Найдите блок:** "Импорт данных из Google Sheets" (выше фильтров)

4. **Нажмите:**
   - "Предпросмотр" - увидите первые 10 записей
   - "Импортировать" - загрузит все 335 записей в БД

5. **Готово!** Данные появятся в таблице автоматически

---

### Способ 2: API (через curl)

```bash
# Предпросмотр (первые 10 записей)
curl "http://localhost:8000/api/import/google-sheets/preview?gid=396039446&limit=10"

# Импорт всех данных
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"
```

**Ответ после импорта:**
```json
{
  "status": "success",
  "message": "Импортировано 335 провайдеров",
  "imported": 335,
  "skipped": 0,
  "errors": 0,
  "total": 335
}
```

---

### Способ 3: Тестовый скрипт

```bash
cd web_service/backend
python3 test_import_1win.py
```

Этот скрипт покажет:
- ✅ Количество найденных записей
- ✅ Примеры данных (первые 3 записи)
- ✅ Инструкции по импорту

---

## 📊 Что будет импортировано

Из таблицы **gid=396039446** будут импортированы:

- **335 провайдеров** для 1win IN
- **Account Types:** FTD, STD
- **Payment Methods:** UPI, Bank Transfer, Wallet
- **Провайдеры:** okbizaxis, cai-pay.net, gopay-wallet.com, unicapspay.com, и другие

---

## ⚙️ Настройка (если еще не сделано)

### 1. Google Sheets API

Убедитесь, что:
- ✅ Файл `google_credentials.json` существует (уже есть ✓)
- ✅ Service Account email добавлен в редакторы таблицы
- ✅ Google Sheets API и Google Drive API включены

**Проверка:**
```bash
ls google_credentials.json
```

### 2. Запуск сервисов

**Backend:**
```bash
cd web_service/backend
python3 start.py
```

**Frontend:**
```bash
cd web_service/frontend
npm run dev
```

---

## 🎯 Примеры использования

### Импорт через веб-интерфейс

1. Откройте http://localhost:5173
2. Найдите блок импорта
3. Нажмите "Предпросмотр" → проверьте данные
4. Нажмите "Импортировать" → данные появятся в таблице

### Импорт через API

```bash
# Полный импорт
curl -X POST "http://localhost:8000/api/import/google-sheets?gid=396039446"

# Проверка результатов
curl "http://localhost:8000/api/providers?merchant=1win&limit=10"
```

---

## ✨ После импорта

После успешного импорта:

1. ✅ **Данные в БД** - сохранены в `providers_data.db`
2. ✅ **В таблице** - отображаются автоматически
3. ✅ **В статистике** - учитываются в графиках
4. ✅ **В фильтрах** - можно фильтровать по `merchant=1win`
5. ✅ **WebSocket** - обновления отправляются (если включен)

---

## 🐛 Troubleshooting

### Ошибка: "Файл credentials не найден"
**Решение:** Файл уже существует ✓, проверьте путь в `config.py`

### Ошибка: "Лист не найден"
**Решение:** Убедитесь, что Service Account email добавлен в редакторы таблицы

### Нет данных после импорта
**Решение:** 
1. Проверьте предпросмотр - должен показать 335 записей
2. Проверьте логи backend
3. Убедитесь, что backend запущен

---

## 📚 Документация

- **IMPORT_1WIN.md** - Полное руководство
- **IMPORT_1WIN_QUICK.md** - Краткая инструкция  
- **USAGE_1WIN_IMPORT.md** - Инструкции по использованию
- **FINAL_1WIN_IMPORT.md** - Итоговая сводка

---

## 🎉 Готово!

**Импорт настроен и готов к использованию!**

Попробуйте:
```bash
# Тест
cd web_service/backend
python3 test_import_1win.py

# Или импорт через веб-интерфейс
# http://localhost:5173
```

**335 провайдеров готовы к импорту! 🚀**
