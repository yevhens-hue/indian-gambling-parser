# 🤝 Руководство по внесению вклада

Спасибо за интерес к проекту! Это руководство поможет вам внести свой вклад.

## 📋 Содержание

- [Как внести вклад](#как-внести-вклад)
- [Процесс разработки](#процесс-разработки)
- [Стандарты кода](#стандарты-кода)
- [Тестирование](#тестирование)
- [Коммиты](#коммиты)
- [Pull Request](#pull-request)

## 🚀 Как внести вклад

1. **Fork** репозитория
2. **Создайте** ветку для вашей функции (`git checkout -b feature/amazing-feature`)
3. **Зафиксируйте** изменения (`git commit -m 'Add amazing feature'`)
4. **Отправьте** в ветку (`git push origin feature/amazing-feature`)
5. **Откройте** Pull Request

## 💻 Процесс разработки

### Настройка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd indian_gambling_parser

# Backend
cd web_service/backend
python3 -m venv venv
source venv/bin/activate  # или `venv\Scripts\activate` на Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # для разработки

# Frontend
cd web_service/frontend
npm install
```

### Запуск для разработки

```bash
# Backend (в одном терминале)
cd web_service/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (в другом терминале)
cd web_service/frontend
npm run dev
```

## 📐 Стандарты кода

### Python (Backend)

Мы используем следующие инструменты:

- **Black** - форматирование кода
- **isort** - сортировка импортов
- **flake8** - линтинг
- **mypy** - проверка типов
- **pylint** - дополнительный линтинг

#### Запуск проверок

```bash
cd web_service/backend
make format    # Форматирование (black + isort)
make lint      # Линтинг (flake8 + pylint)
make type-check # Проверка типов (mypy)
make check     # Все проверки
```

#### Ручной запуск

```bash
# Форматирование
black app/
isort app/

# Линтинг
flake8 app/
pylint app/

# Проверка типов
mypy app/
```

### TypeScript (Frontend)

- **ESLint** - линтинг
- **TypeScript** - проверка типов
- **Prettier** - форматирование (если настроен)

#### Запуск проверок

```bash
cd web_service/frontend
npm run lint
npm run build  # Проверка TypeScript
```

## 🧪 Тестирование

### Backend тесты

```bash
cd web_service/backend
pytest tests/ -v                    # Все тесты
pytest tests/test_storage.py -v     # Unit тесты
pytest tests/test_api.py -v         # Integration тесты
pytest tests/ --cov=app --cov-report=html  # С покрытием
```

### Frontend тесты

```bash
cd web_service/frontend
npm test
npm run test:coverage  # Если настроено
```

### Перед коммитом

Убедитесь, что все тесты проходят:

```bash
# Backend
pytest tests/ -v

# Frontend
npm run build  # Проверка компиляции
```

## 📝 Коммиты

Используйте понятные сообщения коммитов:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Code formatting
refactor: Code refactoring
test: Add tests
chore: Maintenance tasks
```

Примеры:

```bash
git commit -m "feat: Add batch delete functionality"
git commit -m "fix: Resolve WebSocket connection issue"
git commit -m "docs: Update API documentation"
```

## 🔍 Pull Request

### Перед открытием PR

1. ✅ Все тесты проходят
2. ✅ Код отформатирован (black, isort)
3. ✅ Линтинг проходит (flake8, pylint)
4. ✅ Проверка типов проходит (mypy)
5. ✅ Документация обновлена
6. ✅ Commit messages понятные

### Описание PR

Включите в описание:

- **Что изменилось** - краткое описание изменений
- **Почему** - причина изменений
- **Как протестировать** - инструкции для тестирования
- **Скриншоты** (если применимо) - для UI изменений

Пример:

```markdown
## Описание
Добавлена функциональность массового удаления провайдеров.

## Изменения
- Добавлен endpoint `/api/providers/batch-delete`
- Добавлена валидация для списка ID
- Добавлены тесты

## Тестирование
1. Откройте frontend
2. Выберите несколько провайдеров
3. Нажмите "Удалить выбранные"
4. Проверьте, что провайдеры удалены

## Checklist
- [x] Тесты добавлены
- [x] Документация обновлена
- [x] Линтинг проходит
```

### Процесс ревью

1. Откройте Pull Request
2. Дождитесь автоматических проверок (CI/CD)
3. Исправьте замечания ревьюеров (если есть)
4. После одобрения PR будет влит в main

## 📚 Полезные ссылки

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - Как работает сервис
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектура
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Список улучшений

## ❓ Вопросы?

Если у вас есть вопросы:
- Откройте Issue
- Создайте Discussion
- Свяжитесь с maintainers

---

**Спасибо за вклад!** 🎉
