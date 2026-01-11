#!/bin/bash
# Скрипт для быстрой настройки GitHub

set -e

echo "🔗 Настройка подключения к GitHub"
echo "=================================="
echo ""

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git перед продолжением."
    exit 1
fi

echo "✅ Git установлен: $(git --version)"
echo ""

# Проверка, что мы в Git репозитории
if [ ! -d ".git" ]; then
    echo "📦 Инициализация Git репозитория..."
    git init
    echo "✅ Git репозиторий инициализирован"
fi

echo ""
echo "📋 Текущий статус Git:"
git status --short | head -10 || echo "  (нет изменений)"
echo ""

# Проверка remote
if git remote | grep -q "^origin$"; then
    echo "📡 Текущий remote (origin):"
    git remote -v | grep origin
    echo ""
    read -p "Изменить URL? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Введите новый URL: " NEW_URL
        git remote set-url origin "$NEW_URL"
        echo "✅ Remote обновлен"
    fi
else
    echo "📡 Remote 'origin' не настроен"
    echo ""
    read -p "Добавить remote? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Выберите тип подключения:"
        echo "1) HTTPS (https://github.com/USERNAME/REPO.git)"
        echo "2) SSH (git@github.com:USERNAME/REPO.git)"
        read -p "Ваш выбор (1/2): " CONNECTION_TYPE
        
        read -p "Введите GitHub URL репозитория: " REPO_URL
        
        if [[ "$CONNECTION_TYPE" == "2" ]]; then
            # Проверка SSH ключа
            if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
                echo ""
                echo "⚠️  SSH ключ не найден"
                read -p "Создать SSH ключ? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    read -p "Введите email для SSH ключа: " SSH_EMAIL
                    ssh-keygen -t ed25519 -C "$SSH_EMAIL" -f ~/.ssh/id_ed25519
                    echo ""
                    echo "✅ SSH ключ создан"
                    echo "📋 Добавьте публичный ключ в GitHub:"
                    echo "   https://github.com/settings/keys"
                    echo ""
                    cat ~/.ssh/id_ed25519.pub
                    echo ""
                    read -p "Нажмите Enter после добавления ключа в GitHub..."
                fi
            fi
        fi
        
        git remote add origin "$REPO_URL"
        echo "✅ Remote добавлен: $REPO_URL"
    fi
fi

echo ""
echo "=================================="
echo "📝 Следующие шаги:"
echo ""
echo "1. Убедитесь, что репозиторий создан на GitHub"
echo "2. Добавьте файлы:"
echo "   git add ."
echo ""
echo "3. Создайте коммит:"
echo "   git commit -m 'Initial commit'"
echo ""
echo "4. Отправьте в GitHub:"
echo "   git push -u origin main"
echo ""
echo "   (или 'master' если используется эта ветка)"
echo ""
echo "✅ Настройка завершена!"
