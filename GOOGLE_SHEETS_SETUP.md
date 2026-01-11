# Настройка экспорта в Google Sheets

## Шаг 1: Создание Service Account в Google Cloud

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Перейдите в **APIs & Services** → **Library**
4. Найдите и включите **Google Sheets API** и **Google Drive API**
5. Перейдите в **APIs & Services** → **Credentials**
6. Нажмите **Create Credentials** → **Service Account**
7. Заполните данные и создайте аккаунт
8. Нажмите на созданный Service Account
9. Перейдите на вкладку **Keys**
10. Нажмите **Add Key** → **Create new key** → **JSON**
11. Скачайте JSON файл и сохраните его как `google_credentials.json` в папке проекта

## Шаг 2: Предоставление доступа к Google Таблице

1. Откройте вашу Google Таблицу: https://docs.google.com/spreadsheets/d/1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE
2. Нажмите кнопку **Share** (Поделиться)
3. Скопируйте **email адрес** из JSON файла (поле `client_email`)
4. Добавьте этот email с правами **Editor** (Редактор)
5. Сохраните изменения

## Шаг 3: Установка зависимостей

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

## Шаг 4: Размещение файла credentials

Поместите файл `google_credentials.json` в папку проекта:

```
/Users/yevhen.shaforostov/indian_gambling_parser/google_credentials.json
```

## Шаг 5: Проверка работы

После запуска парсера данные автоматически экспортируются в Google Таблицу.

## Альтернативный способ: через переменные окружения

Вы можете указать путь к credentials через переменную окружения:

```bash
export GOOGLE_CREDENTIALS_PATH="/path/to/google_credentials.json"
export GOOGLE_SHEET_ID="1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE"
```

## Структура данных в Google Sheets

Данные будут записаны в следующем формате:
- Первая строка: заголовки колонок
- Последующие строки: данные о провайдерах
- При каждом экспорте старые данные (кроме заголовков) удаляются и записываются новые

## Troubleshooting

### Ошибка "SpreadsheetNotFound"
- Убедитесь, что Service Account email добавлен в список редакторов таблицы
- Проверьте правильность Google Sheet ID

### Ошибка "Permission denied"
- Проверьте, что включены Google Sheets API и Google Drive API
- Убедитесь, что Service Account имеет права Editor на таблице

### Ошибка "FileNotFoundError"
- Проверьте путь к файлу `google_credentials.json`
- Убедитесь, что файл находится в папке проекта или укажите полный путь



