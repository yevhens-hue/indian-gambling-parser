# 🐳 Установка Docker на macOS

**Дата:** 2026-01-11

---

## 🚀 Варианты установки

### Вариант 1: Docker Desktop (Рекомендуется)

Docker Desktop - официальное приложение для macOS с GUI.

#### Шаг 1: Скачать Docker Desktop

1. Перейдите на официальный сайт: https://www.docker.com/products/docker-desktop/
2. Нажмите "Download for Mac"
3. Выберите версию для вашего процессора:
   - **Apple Silicon (M1/M2/M3)**: Docker.dmg для Apple Silicon
   - **Intel**: Docker.dmg для Intel

#### Шаг 2: Установка

1. Откройте скачанный `.dmg` файл
2. Перетащите Docker в папку Applications
3. Запустите Docker из Applications
4. Следуйте инструкциям установщика
5. Docker запросит разрешения - подтвердите их

#### Шаг 3: Проверка

```bash
docker --version
docker compose version
```

---

### Вариант 2: Установка через Homebrew (Быстрый способ)

Если у вас установлен Homebrew:

```bash
# Установка Docker Desktop через Homebrew
brew install --cask docker

# После установки запустите Docker Desktop
open /Applications/Docker.app

# Проверка
docker --version
docker compose version
```

---

### Вариант 3: Установка только Docker Engine (без GUI)

Для серверного использования (требует Homebrew):

```bash
# Установка Docker
brew install docker

# Установка Docker Compose
brew install docker-compose

# Проверка
docker --version
docker compose version
```

**Примечание:** Этот вариант не включает Docker Desktop GUI и требует дополнительной настройки.

---

## ✅ Проверка установки

После установки выполните:

```bash
# Проверка версии Docker
docker --version

# Проверка версии Docker Compose
docker compose version

# Проверка работы Docker
docker run hello-world
```

Ожидаемый результат:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

## 🔧 Настройка после установки

### Добавление Docker в PATH (если необходимо)

Если команда `docker` не найдена после установки:

```bash
# Для Apple Silicon
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Или для Intel
echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Запуск Docker Desktop

Docker Desktop должен быть запущен для работы команд `docker`:

```bash
# Запуск Docker Desktop
open /Applications/Docker.app

# Проверка статуса
docker info
```

---

## 🚀 После установки

После успешной установки Docker, вы сможете запустить production deployment:

```bash
cd web_service
./deploy_production.sh
```

Или напрямую:

```bash
cd web_service
docker compose up -d
```

---

## ⚠️ Требования

- **macOS 10.15 или новее** (для Docker Desktop)
- **4 GB RAM минимум** (рекомендуется 8 GB)
- **Виртуализация включена** (обычно включена по умолчанию)

---

## 📚 Дополнительные ресурсы

- Официальная документация: https://docs.docker.com/desktop/install/mac-install/
- Docker Desktop для Mac: https://www.docker.com/products/docker-desktop/

---

## 🆘 Устранение неполадок

### Docker не запускается

1. Убедитесь, что Docker Desktop запущен
2. Проверьте системные требования
3. Перезапустите Docker Desktop

### Команда docker не найдена

1. Убедитесь, что Docker Desktop установлен
2. Добавьте Docker в PATH (см. выше)
3. Перезапустите терминал

### Проблемы с виртуализацией

1. Убедитесь, что виртуализация включена в настройках системы
2. Для Apple Silicon это не требуется
3. Для Intel может потребоваться включить виртуализацию в BIOS/UEFI

---

**Дата:** 2026-01-11  
**Статус:** Инструкция по установке Docker
