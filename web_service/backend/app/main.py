"""Главный файл FastAPI приложения"""
import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import CORS_ORIGINS, API_PREFIX, AUTH_ENABLED
from app.api import providers, export, screenshots, websocket, auth
from app.api import import_api, analytics, audit, cache_stats, monitoring
from app.utils.logger import logger
from app.services.metrics import get_metrics_service
from app.utils.sentry_config import init_sentry
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.middleware.compression import CompressionMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.response_cache import ResponseCacheMiddleware
from app.middleware.timeout import TimeoutMiddleware
from app.middleware.performance import PerformanceMonitoringMiddleware
from app.middleware.input_sanitization import InputSanitizationMiddleware
from app.middleware.security_audit import SecurityAuditMiddleware
from app.middleware.ip_filter import IPFilterMiddleware
from app.middleware.query_optimization import QueryOptimizationMiddleware


# Инициализация Sentry (опционально)
if os.getenv("SENTRY_DSN"):
    init_sentry()

# Настройка Rate Limiting (с Redis если доступен)
from app.utils.redis_rate_limiter import get_limiter
limiter = get_limiter()

# Создаем FastAPI приложение
app = FastAPI(
    title="Providers API",
    description="""
    API для управления данными провайдеров платежных систем.
    
    ## Версионирование
    
    API поддерживает версионирование:
    - **v1**: `/api/v1/providers` - Версионированные endpoints
    - **latest**: `/api/providers` - Текущая версия (совместима с v1)
    
    ## Основные возможности
    
    * **Управление провайдерами**: CRUD операции
    * **Экспорт данных**: XLSX, CSV, JSON, PDF
    * **Импорт данных**: Google Sheets
    * **Аналитика**: Статистика и графики
    * **Real-time обновления**: WebSocket
    * **Audit Log**: История изменений
    """,
    version="1.1.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Применяем rate limiter к приложению
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Регистрация глобальных обработчиков ошибок
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов"""
    start_time = __import__('time').time()
    
    # Логируем входящий запрос
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    try:
        response = await call_next(request)
        process_time = __import__('time').time() - start_time
        
        # Логируем ответ
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }
        )
        
        return response
    except Exception as e:
        process_time = __import__('time').time() - start_time
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time_ms": round(process_time * 1000, 2),
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware (должен быть первым для отслеживания всех запросов)
app.add_middleware(RequestIDMiddleware)

# IP Filter middleware (фильтрация по IP адресам)
# Можно настроить через переменные окружения: IP_FILTER_ENABLED, IP_WHITELIST, IP_BLACKLIST
app.add_middleware(IPFilterMiddleware, enabled=False)  # По умолчанию отключен

# Input Sanitization middleware (санитизация входных данных)
app.add_middleware(InputSanitizationMiddleware, max_request_size=10 * 1024 * 1024)  # 10MB

# Security Audit middleware (аудит безопасности)
app.add_middleware(SecurityAuditMiddleware, log_all_requests=False)

# Performance monitoring middleware (мониторинг производительности)
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=1.0)

# Query Optimization middleware (мониторинг БД запросов)
app.add_middleware(QueryOptimizationMiddleware, slow_query_threshold=1.0)

# Timeout middleware (ограничивает время выполнения запросов)
app.add_middleware(TimeoutMiddleware, timeout=30.0)  # 30 секунд

# Security headers middleware (расширенные security headers)
app.add_middleware(SecurityHeadersMiddleware, strict_transport_security=True)

# Response cache middleware (кэширует GET запросы)
app.add_middleware(
    ResponseCacheMiddleware,
    cache_ttl=300,  # 5 минут
    cacheable_paths=["/api/providers", "/api/providers/stats"]  # Кэшируем только эти пути
)

# Compression middleware для уменьшения размера ответов
app.add_middleware(CompressionMiddleware)

# Подключение роутеров
app.include_router(auth.router, prefix=API_PREFIX)
from app.api import health
app.include_router(health.router, prefix="/health")
app.include_router(providers.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(screenshots.router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)
app.include_router(import_api.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(cache_stats.router, prefix=API_PREFIX)
app.include_router(monitoring.router, prefix=f"{API_PREFIX}/monitoring")

# API версионирование (v1)
from app.api.v1 import providers as providers_v1
app.include_router(providers_v1.router, prefix=f"{API_PREFIX}/v1")


@app.get("/")
async def root():
    """Корневой endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Providers API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": API_PREFIX
    }


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint
    
    Использование:
    - Prometheus scraper будет обращаться к /metrics
    - Возвращает метрики в формате Prometheus
    """
    try:
        from app.services.metrics import get_metrics_service
        try:
            from prometheus_client import CONTENT_TYPE_LATEST
        except ImportError:
            CONTENT_TYPE_LATEST = "text/plain"
        
        metrics = get_metrics_service()
        metrics_data = metrics.generate_metrics()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Ошибка в metrics endpoint: {e}", exc_info=True)
        return Response(
            content=b"# Error generating metrics\n",
            media_type="text/plain"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
