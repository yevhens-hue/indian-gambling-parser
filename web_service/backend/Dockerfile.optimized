# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as builder

WORKDIR /app

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Копирование только установленных пакетов из builder
COPY --from=builder /root/.local /root/.local

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание директорий для данных
RUN mkdir -p /app/data /app/screenshots

# Копирование кода приложения
COPY app/ ./app/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
ENV DB_PATH=/app/data/providers_data.db
ENV XLSX_PATH=/app/data/providers_data.xlsx

# Открываем порт
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
