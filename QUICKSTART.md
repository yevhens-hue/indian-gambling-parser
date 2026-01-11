# Быстрый старт

## Установка

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Установите браузеры Playwright
playwright install chromium
```

## Первый запуск

```bash
# Запуск парсера для 1xbet
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com
```

## Что делает парсер

1. ✅ Логинится с креденшиалами из `merchants_config.py`
2. ✅ Переходит на страницу депозита (cashier)
3. ✅ Нажимает кнопку "Make Deposit"
4. ✅ Находит все провайдеры в секции E-WALLETS
5. ✅ Кликает по каждому провайдеру
6. ✅ Перехватывает popup/iframe/network requests
7. ✅ Делает скриншот платёжной формы
8. ✅ Сохраняет данные в БД и экспортирует в XLSX

## Результаты

- **SQLite БД**: `providers_data.db`
- **Excel файл**: `providers_data.xlsx`
- **Скриншоты**: `screenshots/`

## Просмотр результатов

```bash
# Показать все результаты
python3 main_parser_playwright.py --show-results

# Показать результаты для конкретного мерчанта
python3 main_parser_playwright.py --show-results --merchant 1xbet

# Экспортировать в XLSX
python3 main_parser_playwright.py --export-xlsx my_results.xlsx
```

## Headless режим

```bash
python3 main_parser_playwright.py --merchant 1xbet --url https://indian.1xbet.com --headless
```

## Структура данных в XLSX

| Поле | Описание |
|------|----------|
| merchant | ID мерчанта |
| merchant_domain | Домен мерчанта |
| account_type | Тип аккаунта (player) |
| provider_domain | Домен провайдера |
| provider_name | Имя провайдера |
| provider_entry_url | Первый внешний URL |
| final_url | Финальный URL после редиректов |
| cashier_url | URL страницы кэшира |
| screenshot_path | Путь к скриншоту |
| detected_in | Где обнаружен (button_text/iframe/network) |
| payment_method | Метод оплаты (UPI/Card/Wallet) |
| is_iframe | Форма в iframe |
| timestamp_utc | Время создания |

## Настройка креденшиалов

Отредактируйте `merchants_config.py`:

```python
"credentials": {
    "username": "ваш_логин",
    "password": "ваш_пароль",
}
```

## Troubleshooting

**Проблема**: Playwright не установлен
```bash
playwright install chromium
```

**Проблема**: Элементы не находятся
- Запустите без `--headless` для отладки
- Проверьте селекторы в `merchants_config.py`

**Проблема**: Провайдеры не найдены
- Убедитесь, что кнопка "Make Deposit" нажата
- Проверьте, что секция E-WALLETS видна

