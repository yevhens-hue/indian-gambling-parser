#!/bin/bash
set -e
PROJECT_DIR="/Users/yevhen.shaforostov/indian_gambling_parser"
cd "$PROJECT_DIR" || exit 1
DATE=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="indian_gambling_parser_backup_${DATE}.tar.gz"
ARCHIVE_PATH="${PROJECT_DIR}/../${ARCHIVE_NAME}"
echo "📦 Создание архива проекта..."
tar -czf "$ARCHIVE_PATH" --exclude="__pycache__" --exclude="*.pyc" --exclude=".git" --exclude="node_modules" --exclude="venv" --exclude=".venv" --exclude=".vscode" --exclude=".idea" --exclude="build" --exclude="dist" --exclude=".pytest_cache" --exclude=".DS_Store" --exclude="*.log" --exclude="*.tar.gz" --exclude="*.zip" -C "$(dirname "$PROJECT_DIR")" "$(basename "$PROJECT_DIR")" 2>&1 | grep -v "Removing leading" || true
ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
echo "✅ Архив создан: $ARCHIVE_NAME"
echo "📊 Размер: $ARCHIVE_SIZE"
echo "📍 Путь: $ARCHIVE_PATH"
