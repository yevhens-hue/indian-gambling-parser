# Парсер провайдеров гемблинговых сайтов Индии

Профессиональный парсер для автоматического сбора данных о платёжных провайдерах на сайтах мерчантов индийского рынка.

## 📁 Структура проекта

```
indian_gambling_parser/
├── provider_parser_playwright.py  # Основной парсер на Playwright
├── storage.py                     # Работа с БД и экспорт в XLSX
├── main_parser_playwright.py     # CLI запускатор
├── merchants_config.py            # Конфигурация мерчантов и креденшиалы
├── requirements.txt               # Зависимости
│
├── README_PLAYWRIGHT.md          # Полная документация
├── HUMAN_IN_THE_LOOP.md          # Документация по human-in-the-loop
├── QUICKSTART.md                 # Быстрый старт
├── ИНСТРУКЦИЯ.md                 # Инструкция на русском
├── ЧТО_ДЕЛАТЬ.txt                # Краткая инструкция
│
├── screenshots/                  # Скриншоты платёжных форм
├── storage_states/               # Сохранённые cookies (storageState)
├── traces/                       # Trace файлы для отладки
│
├── providers_data.db             # SQLite база данных
└── providers_data.xlsx           # Excel экспорт результатов
```

## 🚀 Быстрый старт

### 1. Установка

```bash
cd indian_gambling_parser
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка креденшиалов

Отредактируйте `merchants_config.py`:

```python
"credentials": {
    "username": "ваш_логин",
    "password": "ваш_пароль",
}
```

### 3. Запуск

```bash
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
```

## 📋 Основные команды

```bash
# Запуск парсера
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com

# Запуск в headless режиме
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com --headless

# Просмотр результатов
python3 main_parser_playwright.py --show-results

# Экспорт в Excel
python3 main_parser_playwright.py --export-xlsx results.xlsx

# Список доступных мерчантов
python3 main_parser_playwright.py --list-merchants
```

## 🔐 Human-in-the-Loop

Парсер поддерживает механизм ручного решения капчи:
- При обнаружении капчи парсер останавливается
- Пользователь решает капчу вручную
- После логина сохраняется storageState (cookies)
- При следующих запусках используется сохранённый storageState

Подробнее: см. `HUMAN_IN_THE_LOOP.md`

## 📊 Структура данных

Парсер собирает следующие данные:
- `merchant` - ID мерчанта
- `merchant_domain` - Домен мерчанта
- `account_type` - Тип аккаунта
- `provider_domain` - Домен провайдера
- `provider_name` - Имя провайдера
- `provider_entry_url` - Первый внешний URL
- `final_url` - Финальный URL после редиректов
- `cashier_url` - URL страницы кэшира
- `screenshot_path` - Путь к скриншоту
- `detected_in` - Где обнаружен (button_text/iframe/network)
- `payment_method` - Метод оплаты (UPI/Card/Wallet)
- `is_iframe` - Форма в iframe
- `timestamp_utc` - Время создания

## 🛠️ Технологии

- **Playwright** - автоматизация браузера
- **SQLite** - база данных
- **pandas/openpyxl** - экспорт в Excel
- **tldextract** - нормализация доменов

## 📝 Документация

- `README_PLAYWRIGHT.md` - полная документация
- `QUICKSTART.md` - быстрый старт
- `HUMAN_IN_THE_LOOP.md` - механизм human-in-the-loop
- `ИНСТРУКЦИЯ.md` - инструкция на русском

## ⚠️ Важно

- Креденшиалы хранятся в `merchants_config.py` (для продакшена используйте секрет-хранилище)
- Скриншоты могут содержать PII - обеспечьте контроль доступа
- Логи не выводят пароли/токены

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в терминале
2. Просмотрите trace файлы: `playwright show-trace traces/*.zip`
3. Проверьте скриншоты в папке `screenshots/`



