# 📊 Расширенная аналитика

## ✅ Реализовано

### 1. Dashboard с ключевыми метриками
- ✅ Общее количество провайдеров
- ✅ Новые провайдеры за сегодня
- ✅ Новые провайдеры за последние 7 дней
- ✅ Количество активных merchants
- ✅ Топ merchants и провайдеров
- ✅ Графики трендов по времени
- ✅ Распределение по типам аккаунтов
- ✅ Распределение по методам оплаты

### 2. API Endpoints

#### GET `/api/analytics/dashboard`
Получить ключевые метрики для dashboard

**Параметры:**
- `days` (int, default: 7) - Количество дней для анализа

**Пример:**
```bash
curl "http://localhost:8000/api/analytics/dashboard?days=30"
```

**Ответ:**
```json
{
  "total_providers": 335,
  "new_today": 5,
  "new_last_7_days": 42,
  "active_merchants": 3,
  "top_merchants": [
    {"name": "1win", "count": 250},
    {"name": "1xbet", "count": 50}
  ],
  "top_providers": [
    {"name": "okbizaxis", "count": 120},
    {"name": "cai-pay.net", "count": 80}
  ],
  "trends": [
    {"date": "2026-01-10", "count": 15},
    {"date": "2026-01-09", "count": 12}
  ],
  "account_types_distribution": {
    "FTD": 200,
    "STD": 135
  },
  "payment_methods_distribution": {
    "UPI": 280,
    "Bank Transfer": 55
  }
}
```

#### GET `/api/analytics/trends`
Получить тренды по провайдерам за период

**Параметры:**
- `period` (string) - Период: `1d`, `7d`, `30d`, `90d`, `1y`, `all`
- `group_by` (string) - Группировка: `day`, `week`, `month`

**Пример:**
```bash
curl "http://localhost:8000/api/analytics/trends?period=30d&group_by=day"
```

#### GET `/api/analytics/comparison`
Сравнение merchants по метрикам

**Параметры:**
- `merchants` (string) - Список merchants через запятую

**Пример:**
```bash
curl "http://localhost:8000/api/analytics/comparison?merchants=1win,1xbet"
```

#### GET `/api/analytics/provider-details/{provider_domain}`
Детальная аналитика по конкретному провайдеру

**Параметры:**
- `provider_domain` (path) - Домен провайдера
- `days` (int, default: 30) - Период анализа

**Пример:**
```bash
curl "http://localhost:8000/api/analytics/provider-details/okbizaxis?days=90"
```

---

## 🎯 Использование в UI

### Доступ к Dashboard

1. Откройте http://localhost:5173
2. Перейдите на вкладку **"📊 Analytics Dashboard"**
3. Выберите период анализа (7, 30, 90, 365 дней)
4. Просматривайте метрики и графики

### Вкладки в интерфейсе

- **📋 Данные** - Таблица с данными провайдеров (как было)
- **📊 Analytics Dashboard** - Новый dashboard с аналитикой

---

## 📈 Доступные графики

### 1. Ключевые метрики (карточки)
- Всего провайдеров
- Новых сегодня
- За 7 дней
- Активных merchants

### 2. График трендов
- Area chart показывающий динамику добавления провайдеров по дням
- Адаптивный период (7-365 дней)

### 3. Распределение по типам аккаунтов
- Bar chart с количеством провайдеров по типам (FTD, STD)

### 4. Топ Merchants
- Bar chart с топ-10 merchants по количеству провайдеров

### 5. Топ провайдеров
- Bar chart с топ-10 провайдеров по частоте использования

### 6. Методы оплаты
- Bar chart с распределением по payment methods

---

## 🔄 Автоматическое обновление

- **Метрики:** Обновляются каждые 30 секунд
- **Тренды:** Обновляются каждую минуту
- **Real-time:** Данные обновляются через WebSocket при изменениях в БД

---

## 📊 Примеры использования

### Получить статистику за последний месяц

```bash
curl "http://localhost:8000/api/analytics/dashboard?days=30"
```

### Сравнить двух merchants

```bash
curl "http://localhost:8000/api/analytics/comparison?merchants=1win,1xbet"
```

### Детальная аналитика по провайдеру

```bash
curl "http://localhost:8000/api/analytics/provider-details/okbizaxis?days=90"
```

### Тренды за последний год

```bash
curl "http://localhost:8000/api/analytics/trends?period=1y&group_by=month"
```

---

## 🎨 Визуализация

### Типы графиков:
- **Area Chart** - для трендов во времени
- **Bar Chart** - для сравнения категорий
- **Карточки** - для ключевых метрик

### Цветовая схема:
- Синий (#8884d8) - основная статистика
- Зеленый (#82ca9d) - типы аккаунтов
- Оранжевый (#ffc658) - топ провайдеры
- Красный (#ff7300) - методы оплаты

---

## ⚙️ Настройка периодов

### Доступные периоды для трендов:
- `1d` - Последний день
- `7d` - Последняя неделя
- `30d` - Последний месяц
- `90d` - Последние 3 месяца
- `1y` - Последний год
- `all` - Все время

### Группировка:
- `day` - По дням
- `week` - По неделям
- `month` - По месяцам

---

## 🧪 Тестирование

### Проверка API:

```bash
# Dashboard метрики
curl "http://localhost:8000/api/analytics/dashboard?days=7"

# Тренды
curl "http://localhost:8000/api/analytics/trends?period=30d&group_by=day"

# Сравнение
curl "http://localhost:8000/api/analytics/comparison?merchants=1win"

# Детали провайдера
curl "http://localhost:8000/api/analytics/provider-details/okbizaxis"
```

### Через Swagger UI:

1. Откройте http://localhost:8000/docs
2. Найдите секцию **analytics**
3. Протестируйте endpoints

---

## 📚 Дополнительные возможности

### Экспорт аналитики

Можно добавить экспорт аналитических данных:
- CSV с метриками
- JSON с детальной аналитикой
- PDF отчеты (будущее)

### Расширенная фильтрация

Можно фильтровать аналитику по:
- Конкретным merchants
- Периодам времени
- Типам аккаунтов
- Методам оплаты

---

**Аналитика готова к использованию! 📊🚀**
