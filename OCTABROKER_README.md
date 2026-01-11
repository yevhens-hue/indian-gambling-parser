# Парсер для Octa Broker

## Конфигурация

Мерчант **octabroker** добавлен в проект. Парсер работает аналогично парсеру для 1xbet, но адаптирован для структуры сайта Octa Broker.

## Креденшиалы

- **Email**: `kapil.ss17@yahoo.in`
- **Password**: `Butterfly@24`

## Запуск

```bash
python3 main_parser_playwright.py --merchant octabroker --url https://www.octabroker.com
```

## Особенности

- ✅ **Нет капчи** - логин происходит автоматически без ручного вмешательства
- ✅ Автоматическое сохранение cookies в `storage_states/octabroker_storage_state.json`
- ✅ Поиск и обработка провайдеров платежей
- ✅ Заполнение форм провайдеров
- ✅ Сохранение результатов в БД и Google Sheets

## Что делает парсер

1. **Автоматический логин** с креденшиалами из конфига
2. **Переход на страницу депозита** (найдёт автоматически)
3. **Поиск провайдеров платежей** на странице депозита
4. **Обработка каждого провайдера**:
   - Клик по провайдеру
   - Заполнение полей формы (UPI ID, Phone, Aadhaar, Full Name)
   - Нажатие кнопки подтверждения
   - Сохранение скриншотов и данных

## Результаты

- **SQLite БД**: `providers_data.db`
- **Excel файл**: `providers_data.xlsx`
- **Скриншоты**: `screenshots/`
- **Cookies**: `storage_states/octabroker_storage_state.json`

## Просмотр результатов

```bash
# Показать все результаты для octabroker
python3 main_parser_playwright.py --show-results --merchant octabroker

# Экспортировать в XLSX
python3 main_parser_playwright.py --export-xlsx octabroker_results.xlsx
```

## Настройка селекторов

Если парсер не находит элементы на странице Octa Broker, можно уточнить селекторы в `merchants_config.py` в секции `"octabroker"` → `"selectors"`.

## Troubleshooting

**Проблема**: Логин не работает
- Проверьте креденшиалы в `merchants_config.py`
- Убедитесь, что селекторы для логина корректны

**Проблема**: Провайдеры не найдены
- Проверьте селекторы `provider_buttons` и `provider_links` в конфиге
- Запустите без `--headless` для отладки



