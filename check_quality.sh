#!/bin/bash
# Скрипт проверки качества кода перед деплоем

set -e

echo "🔍 Проверка качества кода"
echo "=========================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Проверка тестов
echo "📝 Запуск тестов..."
if python3 -m pytest tests/ -v --tb=short > /tmp/test_output.txt 2>&1; then
    TESTS_PASSED=$(grep -c "PASSED" /tmp/test_output.txt || echo "0")
    TESTS_FAILED=$(grep -c "FAILED" /tmp/test_output.txt || echo "0")
    echo -e "${GREEN}✅ Тесты пройдены: $TESTS_PASSED passed${NC}"
    if [ "$TESTS_FAILED" -gt 0 ]; then
        echo -e "${RED}❌ Тесты провалены: $TESTS_FAILED failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Тесты провалены${NC}"
    cat /tmp/test_output.txt | tail -30
    exit 1
fi
echo ""

# 2. Проверка безопасности
echo "🔒 Проверка безопасности (bandit)..."
if command -v bandit &> /dev/null; then
    if python3 -m bandit -r web_service/backend/app storage.py -f txt -ll 2>&1 | grep -q "High:"; then
        HIGH_ISSUES=$(python3 -m bandit -r web_service/backend/app storage.py -f txt -ll 2>&1 | grep "High:" | awk '{print $2}')
        echo -e "${RED}❌ Найдены критические уязвимости: $HIGH_ISSUES${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Критические уязвимости не найдены${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  bandit не установлен, пропускаем${NC}"
fi
echo ""

# 3. Проверка покрытия тестами
echo "📊 Проверка покрытия тестами..."
if command -v coverage &> /dev/null; then
    COVERAGE=$(python3 -m pytest tests/ --cov=web_service/backend/app --cov-report=term 2>&1 | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
    if (( $(echo "$COVERAGE >= 40" | bc -l) )); then
        echo -e "${GREEN}✅ Покрытие: ${COVERAGE}%${NC}"
    else
        echo -e "${YELLOW}⚠️  Покрытие: ${COVERAGE}% (рекомендуется >40%)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  coverage не установлен, пропускаем${NC}"
fi
echo ""

# 4. Проверка синтаксиса Python
echo "🐍 Проверка синтаксиса Python..."
if python3 -m py_compile web_service/backend/app/**/*.py storage.py 2>&1; then
    echo -e "${GREEN}✅ Синтаксис корректен${NC}"
else
    echo -e "${RED}❌ Ошибки синтаксиса${NC}"
    exit 1
fi
echo ""

# 5. Проверка наличия основных файлов
echo "📁 Проверка структуры проекта..."
REQUIRED_FILES=(
    "web_service/backend/app/main.py"
    "web_service/backend/requirements.txt"
    "render.yaml"
    "DEPLOY.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Отсутствует: $file${NC}"
        exit 1
    fi
done
echo ""

echo "=========================="
echo -e "${GREEN}✅ Все проверки пройдены!${NC}"
echo "Проект готов к деплою 🚀"
