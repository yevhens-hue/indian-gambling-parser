# 🔗 Подключение к GitHub

**Дата:** 2026-01-11

---

## 📋 Инструкции по подключению к GitHub

### Вариант 1: Создать новый репозиторий на GitHub

1. **Создайте репозиторий на GitHub:**
   - Перейдите на https://github.com/new
   - Название: `indian-gambling-parser` (или другое)
   - Описание: "Web service for managing payment providers data"
   - Тип: Public или Private
   - **НЕ** добавляйте README, .gitignore или license (они уже есть)

2. **Подключите локальный репозиторий:**

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser

# Проверьте текущие remotes
git remote -v

# Если remote уже есть, используйте:
# git remote set-url origin https://github.com/YOUR_USERNAME/indian-gambling-parser.git

# Если remote нет, добавьте:
git remote add origin https://github.com/YOUR_USERNAME/indian-gambling-parser.git

# Или через SSH (если настроен):
# git remote add origin git@github.com:YOUR_USERNAME/indian-gambling-parser.git
```

3. **Зафиксируйте изменения и отправьте:**

```bash
# Добавьте все файлы
git add .

# Создайте коммит
git commit -m "feat: Initial commit with all improvements

- Global error handling
- API versioning (v1)
- Enhanced OpenAPI documentation
- Additional unit tests
- Docker optimization
- Production deployment ready"

# Отправьте в GitHub (первый раз)
git push -u origin main

# Или если ветка называется master:
# git push -u origin master
```

---

### Вариант 2: Использовать существующий репозиторий

Если репозиторий уже существует на GitHub:

```bash
cd /Users/yevhen.shaforostov/indian_gambling_parser

# Проверьте текущий remote
git remote -v

# Если нужно изменить URL:
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Или добавить новый remote:
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Проверьте текущую ветку
git branch

# Отправьте изменения
git push -u origin main
```

---

### Вариант 3: SSH подключение (рекомендуется)

1. **Проверьте наличие SSH ключа:**

```bash
ls -la ~/.ssh/id_rsa.pub
```

2. **Если ключа нет, создайте его:**

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Нажмите Enter для всех вопросов (или задайте пароль)

# Покажите публичный ключ
cat ~/.ssh/id_rsa.pub
```

3. **Добавьте ключ в GitHub:**
   - Перейдите: https://github.com/settings/keys
   - Нажмите "New SSH key"
   - Скопируйте содержимое `~/.ssh/id_rsa.pub`
   - Вставьте и сохраните

4. **Используйте SSH URL:**

```bash
git remote add origin git@github.com:YOUR_USERNAME/indian-gambling-parser.git
```

---

## 🔧 Проверка подключения

### Проверить remote:

```bash
git remote -v
```

Ожидаемый результат:
```
origin  https://github.com/YOUR_USERNAME/indian-gambling-parser.git (fetch)
origin  https://github.com/YOUR_USERNAME/indian-gambling-parser.git (push)
```

### Проверить SSH подключение:

```bash
ssh -T git@github.com
```

Ожидаемый результат:
```
Hi YOUR_USERNAME! You've successfully authenticated...
```

---

## 📝 Полезные команды

### Основные операции:

```bash
# Статус
git status

# Добавить все изменения
git add .

# Коммит
git commit -m "Описание изменений"

# Отправить в GitHub
git push

# Получить изменения
git pull

# Посмотреть историю
git log --oneline -10
```

### Работа с ветками:

```bash
# Создать новую ветку
git checkout -b feature/new-feature

# Переключиться на ветку
git checkout main

# Отправить ветку в GitHub
git push -u origin feature/new-feature
```

---

## 🚀 GitHub Actions (CI/CD)

Если нужно настроить автоматические тесты и сборку:

1. **Файлы уже созданы:**
   - `.github/workflows/ci.yml` - автоматические тесты
   - `.github/workflows/docker.yml` - сборка Docker образов
   - `.github/workflows/release.yml` - автоматические релизы

2. **После push в GitHub:**
   - GitHub Actions автоматически запустятся
   - Тесты будут выполняться при каждом push
   - Docker образы будут собираться автоматически

---

## ⚠️ Важные файлы для .gitignore

Убедитесь, что следующие файлы игнорируются:

- `.env` - секреты
- `*.db` - базы данных
- `*.xlsx` - Excel файлы
- `__pycache__/` - Python кэш
- `node_modules/` - Node.js зависимости
- `.venv/` - виртуальные окружения
- `screenshots/` - скриншоты (если нужно)
- `google_credentials.json` - секреты Google API

---

## 📚 Дополнительные ресурсы

- GitHub Docs: https://docs.github.com
- Git Documentation: https://git-scm.com/doc
- SSH Keys Setup: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

## ✅ Checklist перед push

- [ ] Проверен `.gitignore`
- [ ] Нет секретов в коде (`.env`, пароли, токены)
- [ ] Все тесты проходят
- [ ] Документация актуальна
- [ ] Коммиты понятны и описательны
- [ ] Remote настроен правильно

---

**Дата:** 2026-01-11  
**Статус:** Инструкция по подключению GitHub
