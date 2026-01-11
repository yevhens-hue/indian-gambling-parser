# Парсер провайдеров на Playwright

Профессиональный парсер провайдеров платежных систем для гемблинговых сайтов индийского рынка.

## Особенности

- ✅ **Playwright** - стабильная работа с редиректами, iframe, popup
- ✅ **Перехват network requests** - обнаружение реальных endpoints провайдеров
- ✅ **Обработка iframe** - автоматическое обнаружение форм в iframe
- ✅ **Обработка popup** - перехват новых вкладок
- ✅ **Нормализация доменов** - eTLD+1 для корректной идентификации
- ✅ **Экспорт в XLSX** - удобный формат для анализа
- ✅ **Расширенная структура данных** - все необходимые поля

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Установите браузеры для Playwright:
```bash
playwright install chromium
```

## Структура данных

Парсер собирает следующие данные:

### Обязательные поля:
- `merchant` - идентификатор мерчанта
- `merchant_domain` - домен мерчанта
- `account_type` - тип аккаунта (admin/agent/player/merchant-ops)
- `provider_domain` - домен провайдера (eTLD+1)
- `provider_name` - имя провайдера (из UI)
- `provider_entry_url` - первый внешний URL после клика
- `final_url` - финальный URL после всех редиректов
- `cashier_url` - URL страницы кэшира
- `screenshot_path` - путь к скриншоту платёжной формы
- `detected_in` - где обнаружен (button_text/href/iframe src/network request)
- `timestamp_utc` - время создания записи

### Опциональные поля:
- `payment_method` - метод оплаты (UPI/Card/NetBanking/Wallet)
- `is_iframe` - форма в iframe (True/False)
- `requires_otp` - требуется OTP
- `blocked_by_geo` - заблокирован по гео
- `captcha_present` - присутствует капча

## Использование

### Просмотр доступных мерчантов:
```bash
python3 main_parser_playwright.py --list-merchants
```

### Запуск парсера:
```bash
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
```

### Запуск в headless режиме:
```bash
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com --headless
```

### Просмотр результатов:
```bash
python3 main_parser_playwright.py --show-results
```

### Просмотр результатов конкретного мерчанта:
```bash
python3 main_parser_playwright.py --show-results --merchant 1xbet
```

### Экспорт в XLSX:
```bash
python3 main_parser_playwright.py --export-xlsx results.xlsx
```

## Flow работы парсера

1. **Логин** - вход с креденшиалами
2. **Переход на кэшир** - навигация на страницу депозита
3. **Нажатие "Make Deposit"** - открытие формы выбора провайдеров
4. **Поиск E-WALLETS** - поиск секции с провайдерами
5. **Обработка провайдеров**:
   - Клик по каждой кнопке провайдера
   - Перехват popup/iframe/network requests
   - Определение финального URL провайдера
   - Создание скриншота платёжной формы
   - Сохранение данных в БД

## Технические детали

### Обработка редиректов
Парсер фиксирует:
- `provider_entry_url` - первый внешний URL (может быть трекер)
- `final_url` - финальный URL после всех редиректов
- Домен определяется по `final_url`

### Обработка iframe
- Автоматическое обнаружение iframe с внешними доменами
- Скриншот делается из iframe элемента
- `is_iframe = True` в результатах

### Обработка popup
- Перехват новых вкладок через `page.on("popup")`
- Автоматическое закрытие после обработки
- Скриншот делается из popup страницы

### Перехват network requests
- Мониторинг всех HTTP запросов
- Обнаружение внешних доменов провайдеров
- Используется как fallback если не найден через UI

### Нормализация доменов
- Используется `tldextract` для eTLD+1
- Пример: `subdomain.example.co.in` → `example.co.in`

## Файлы

- `provider_parser_playwright.py` - основной парсер
- `storage.py` - работа с БД и экспорт в XLSX
- `main_parser_playwright.py` - CLI для запуска
- `merchants_config.py` - конфигурация мерчантов
- `providers_data.db` - SQLite база данных
- `providers_data.xlsx` - экспорт в Excel
- `screenshots/` - директория со скриншотами

## Настройка

Перед использованием настройте креденшиалы в `merchants_config.py`:

```python
"credentials": {
    "username": "ваш_логин",
    "password": "ваш_пароль",
}
```

Также можно настроить селекторы для каждого мерчанта.

## Безопасность

⚠️ **Важно:**
- Креденшиалы хранятся в конфигурационном файле (для продакшена используйте секрет-хранилище)
- Скриншоты могут содержать PII - обеспечьте контроль доступа
- Логи не выводят пароли/токены

## Примеры использования

### Базовый запуск:
```python
from provider_parser_playwright import ProviderParserPlaywright

parser = ProviderParserPlaywright(headless=True)
results = await parser.parse_merchant("1xbet", "https://indian.1xbet.com", headless=True)
```

### Просмотр результатов:
```python
from storage import Storage

storage = Storage()
results = storage.get_all_providers("1xbet")
for row in results:
    print(f"{row['provider_domain']} - {row['final_url']}")
```

## Troubleshooting

### Проблема: Playwright не находит элементы
- Увеличьте timeout в селекторах
- Проверьте, что страница полностью загрузилась
- Используйте `--headless=false` для отладки

### Проблема: Провайдеры не найдены
- Проверьте селекторы в `merchants_config.py`
- Убедитесь, что кнопка "Make Deposit" нажата
- Проверьте, что секция E-WALLETS видна на странице

### Проблема: Скриншоты не создаются
- Проверьте права на запись в директорию `screenshots/`
- Убедитесь, что iframe/popup успешно открылись

