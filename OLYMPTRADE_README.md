# Парсер для Olymptrade

## Описание

Специальный парсер для сайта Olymptrade с пошаговым флоу:
1. Логин с креденшиалами
2. Нажатие на кнопку "Payments"
3. Нажатие на кнопку "Deposit"
4. Нажатие на кнопку "Next"
5. Заполнение полей формы
6. Нажатие на кнопку "Proceed to payment"
7. Скриншот и сохранение URL
8. Экспорт в Google Sheets

## Креденшиалы

- **Email**: `rencruise961@gmail.com`
- **Password**: `Ren@Cruise01`

## Данные для заполнения формы

- **First Name**: `kapil`
- **Last Name**: `Sharma`
- **Phone**: `8925242020`
- **UPI ID**: `kapil.ss17@icici`

## Запуск

```bash
python3 main_parser_playwright.py --merchant olymptrade --url https://olymptrade.com/platform
```

## Что делает парсер

### Шаг 1: Переход на платформу
- Открывает браузер и переходит на `https://olymptrade.com/platform`

### Шаг 2: Логин
- Находит кнопку "LogIn"
- Вводит email и password
- Нажимает кнопку входа
- Сохраняет cookies для следующих запусков

### Шаг 3: Нажатие "Payments"
- Ищет и нажимает кнопку "Payments" в интерфейсе

### Шаг 4: Нажатие "Deposit"
- В открывшейся панели нажимает кнопку "Deposit"

### Шаг 5: Нажатие "Next"
- В новой панели нажимает кнопку "Next"

### Шаг 6: Заполнение формы
- Заполняет поля:
  - First Name: `kapil`
  - Last Name: `Sharma`
  - Phone: `8925242020`
  - UPI ID: `kapil.ss17@icici`

### Шаг 7: Нажатие "Proceed to payment"
- Нажимает кнопку "Proceed to payment"
- Ожидает редирект на страницу провайдера

### Шаг 8: Скриншот и сохранение
- Делает скриншот страницы после редиректа
- Сохраняет URL страницы провайдера
- Сохраняет данные в БД
- Экспортирует в Google Sheets

## Результаты

- **SQLite БД**: `providers_data.db`
- **Excel файл**: `providers_data.xlsx`
- **Скриншоты**: `screenshots/olymptrade.com_olymptrade_*.png`
- **Cookies**: `storage_states/olymptrade_storage_state.json`
- **Google Sheets**: `https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE/edit?gid=287244309#gid=287244309`

## Просмотр результатов

```bash
# Показать все результаты для olymptrade
python3 main_parser_playwright.py --show-results --merchant olymptrade

# Экспортировать в XLSX
python3 main_parser_playwright.py --export-xlsx olymptrade_results.xlsx
```

## Особенности

- ✅ **Автоматический логин** без капчи
- ✅ **Пошаговый флоу** с точными шагами
- ✅ **Автоматическое заполнение** всех полей формы
- ✅ **Скриншот** страницы провайдера
- ✅ **Автоматический экспорт** в Google Sheets

## Troubleshooting

**Проблема**: Кнопка не найдена
- Проверьте селекторы в `merchants_config.py` в секции `"olymptrade"` → `"selectors"`
- Запустите без `--headless` для отладки
- Убедитесь, что страница полностью загрузилась

**Проблема**: Поля не заполняются
- Проверьте селекторы полей в конфиге
- Убедитесь, что форма видна на странице
- Проверьте, что кнопка "Next" была нажата

**Проблема**: Редирект не происходит
- Убедитесь, что все поля заполнены корректно
- Проверьте, что кнопка "Proceed to payment" была нажата
- Увеличьте таймаут ожидания редиректа



