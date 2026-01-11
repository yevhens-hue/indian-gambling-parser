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
from app.api import import_api, analytics, audit
from app.utils.logger import logger
from app.services.metrics import get_metrics_service
from app.utils.sentry_config import init_sentry
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Опциональная зависимость для health checks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Инициализация Sentry (опционально)
if os.getenv("SENTRY_DSN"):
    init_sentry()

# Настройка Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

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

# Подключение роутеров
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(providers.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(screenshots.router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)
app.include_router(import_api.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)

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


@app.get("/health")
async def health_check():
    """
    Health check endpoint с детальными проверками
    
    Returns:
        - status: ok/unhealthy
        - checks: результаты проверок компонентов
        - timestamp: время проверки
    """
    checks = {}
    all_healthy = True
    
    # Проверка БД
    try:
        from app.services.storage_adapter import StorageAdapter
        adapter = StorageAdapter()
        providers = adapter.storage.get_all_providers(merchant=None)
        checks["database"] = {
            "status": "ok",
            "message": f"Connected, {len(providers)} providers",
            "providers_count": len(providers)
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "message": str(e)
        }
        all_healthy = False
    
    # Проверка Redis (опционально)
    try:
        from app.services.cache import get_cache_service
        cache = get_cache_service()
        checks["cache"] = {
            "status": "ok" if cache.enabled else "disabled",
            "message": "Enabled" if cache.enabled else "Redis not available (optional)",
            "enabled": cache.enabled
        }
    except Exception as e:
        checks["cache"] = {
            "status": "disabled",
            "message": f"Redis not available: {str(e)} (optional)"
        }
    
    # Проверка дискового пространства (если psutil доступен)
    if PSUTIL_AVAILABLE:
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            checks["disk"] = {
                "status": "ok" if free_percent > 10 else "warning",
                "message": f"{free_percent:.1f}% free",
                "free_percent": round(free_percent, 1),
                "free_gb": round(disk_usage.free / (1024**3), 2)
            }
            if free_percent < 10:
                all_healthy = False
        except Exception as e:
            checks["disk"] = {
                "status": "unknown",
                "message": f"Check failed: {str(e)}"
            }
        
        # Проверка памяти
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            checks["memory"] = {
                "status": "ok" if memory_percent < 90 else "warning",
                "message": f"{memory_percent:.1f}% used",
                "used_percent": round(memory_percent, 1),
                "available_gb": round(memory.available / (1024**3), 2)
            }
            if memory_percent > 95:
                all_healthy = False
        except Exception as e:
            checks["memory"] = {
                "status": "unknown",
                "message": f"Check failed: {str(e)}"
            }
    else:
        checks["disk"] = {
            "status": "disabled",
            "message": "psutil not available (optional)"
        }
        checks["memory"] = {
            "status": "disabled",
            "message": "psutil not available (optional)"
        }
    
    status = "ok" if all_healthy else "unhealthy"
    
    logger.debug(f"Health check: {status}", extra={"checks": checks})
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
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
