#!/bin/bash
# Скрипт для установки Docker на macOS

set -e

echo "🐳 Установка Docker на macOS"
echo "=============================="
echo ""

# Проверка операционной системы
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Этот скрипт предназначен для macOS"
    exit 1
fi

# Проверка архитектуры
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    echo "✅ Обнаружен Apple Silicon (ARM64)"
    DOCKER_ARCH="Apple Silicon"
elif [[ "$ARCH" == "x86_64" ]]; then
    echo "✅ Обнаружен Intel (x86_64)"
    DOCKER_ARCH="Intel"
else
    echo "⚠️  Неизвестная архитектура: $ARCH"
    DOCKER_ARCH="Universal"
fi

echo ""

# Проверка наличия Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker уже установлен"
    docker --version
    echo ""
    read -p "   Продолжить установку? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Проверка Homebrew
if command -v brew &> /dev/null; then
    echo "✅ Homebrew найден"
    echo ""
    echo "📦 Установка Docker Desktop через Homebrew..."
    echo ""
    read -p "   Продолжить установку через Homebrew? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔧 Установка Docker Desktop..."
        brew install --cask docker
        
        echo ""
        echo "✅ Docker Desktop установлен!"
        echo ""
        echo "🚀 Запуск Docker Desktop..."
        open /Applications/Docker.app
        
        echo ""
        echo "⏳ Ожидание запуска Docker (10 секунд)..."
        sleep 10
        
        echo ""
        echo "✅ Проверка установки..."
        if docker --version &> /dev/null; then
            echo "✅ Docker установлен и работает!"
            docker --version
            docker compose version
        else
            echo "⚠️  Docker установлен, но еще не запущен"
            echo "   Запустите Docker Desktop вручную:"
            echo "   open /Applications/Docker.app"
        fi
        
        exit 0
    fi
fi

# Если Homebrew не найден или пользователь отказался
echo ""
echo "📥 Установка Docker Desktop вручную"
echo "===================================="
echo ""
echo "1. Откройте браузер и перейдите:"
echo "   https://www.docker.com/products/docker-desktop/"
echo ""
echo "2. Скачайте Docker Desktop для Mac ($DOCKER_ARCH)"
echo ""
echo "3. Откройте скачанный .dmg файл"
echo ""
echo "4. Перетащите Docker в папку Applications"
echo ""
echo "5. Запустите Docker из Applications"
echo ""
echo "6. После установки проверьте:"
echo "   docker --version"
echo ""
echo "7. Затем запустите deployment:"
echo "   cd web_service"
echo "   ./deploy_production.sh"
echo ""

# Попытка открыть браузер
read -p "   Открыть страницу загрузки в браузере? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://www.docker.com/products/docker-desktop/"
fi

echo ""
echo "✅ Инструкции показаны"
