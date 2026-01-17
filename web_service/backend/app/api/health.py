"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from app.models.health import HealthResponse, HealthCheck
from app.services.storage_adapter import StorageAdapter
from app.services.cache import get_cache_service
from app.utils.logger import logger
import os
from datetime import datetime

# psutil опционален
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

router = APIRouter(tags=["health"])


def check_database() -> HealthCheck:
    """Проверка подключения к базе данных"""
    try:
        storage = StorageAdapter()
        result = storage.get_all_providers(limit=1)
        total = result.get("total", 0)
        
        return HealthCheck(
            status="ok",
            message=f"Connected, {total} providers"
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return HealthCheck(
            status="error",
            message=f"Connection failed: {str(e)}"
        )


def check_cache() -> HealthCheck:
    """Проверка кэша"""
    try:
        cache_service = get_cache_service()
        if cache_service.enabled:
            # Пробуем записать и прочитать тестовое значение
            test_key = "health_check_test"
            cache_service.set(test_key, "test", ttl=10)
            value = cache_service.get(test_key)
            cache_service.delete(test_key)
            
            if value == "test":
                return HealthCheck(
                    status="ok",
                    message="Cache is working",
                    enabled=True
                )
            else:
                return HealthCheck(
                    status="warning",
                    message="Cache read/write test failed",
                    enabled=True
                )
        else:
            return HealthCheck(
                status="ok",
                message="Cache disabled",
                enabled=False
            )
    except Exception as e:
        logger.error(f"Cache health check failed: {e}", exc_info=True)
        return HealthCheck(
            status="error",
            message=f"Cache check failed: {str(e)}",
            enabled=False
        )


def check_disk_space() -> HealthCheck:
    """Проверка свободного места на диске"""
    if not PSUTIL_AVAILABLE:
        return HealthCheck(
            status="unknown",
            message="psutil not installed"
        )
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        percent_free = (disk.free / disk.total) * 100
        
        if percent_free < 10:
            status = "error"
            message = f"Low disk space: {free_gb:.2f}GB free ({percent_free:.1f}%)"
        elif percent_free < 20:
            status = "warning"
            message = f"Disk space: {free_gb:.2f}GB free ({percent_free:.1f}%)"
        else:
            status = "ok"
            message = f"Disk space: {free_gb:.2f}GB free ({percent_free:.1f}%)"
        
        return HealthCheck(
            status=status,
            message=message,
            details={
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_free": round(percent_free, 1)
            }
        )
    except Exception as e:
        logger.error(f"Disk space check failed: {e}", exc_info=True)
        return HealthCheck(
            status="error",
            message=f"Disk check failed: {str(e)}"
        )


def check_memory() -> HealthCheck:
    """Проверка использования памяти"""
    if not PSUTIL_AVAILABLE:
        return HealthCheck(
            status="unknown",
            message="psutil not installed"
        )
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        available_gb = memory.available / (1024 ** 3)
        
        if used_percent > 90:
            status = "error"
            message = f"High memory usage: {used_percent:.1f}%"
        elif used_percent > 80:
            status = "warning"
            message = f"Memory usage: {used_percent:.1f}%"
        else:
            status = "ok"
            message = f"Memory usage: {used_percent:.1f}%"
        
        return HealthCheck(
            status=status,
            message=message,
            details={
                "used_percent": round(used_percent, 1),
                "available_gb": round(available_gb, 2)
            }
        )
    except Exception as e:
        logger.error(f"Memory check failed: {e}", exc_info=True)
        return HealthCheck(
            status="error",
            message=f"Memory check failed: {str(e)}"
        )


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Базовый health check endpoint
    """
    checks = {
        "database": check_database(),
        "cache": check_cache(),
    }
    
    # Определяем общий статус
    all_ok = all(check.status == "ok" for check in checks.values())
    overall_status = "ok" if all_ok else "degraded"
    
    return HealthResponse(
        status=overall_status,
        checks=checks,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    Детальный health check с проверкой всех систем
    """
    checks = {
        "database": check_database(),
        "cache": check_cache(),
        "disk_space": check_disk_space(),
        "memory": check_memory(),
    }
    
    # Определяем общий статус
    statuses = [check.status for check in checks.values()]
    if "error" in statuses:
        overall_status = "error"
    elif "warning" in statuses:
        overall_status = "warning"
    else:
        overall_status = "ok"
    
    return HealthResponse(
        status=overall_status,
        checks=checks,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe для Kubernetes/Docker
    Проверяет, готов ли сервис принимать трафик
    """
    checks = {
        "database": check_database(),
    }
    
    # Сервис готов, если база данных доступна
    is_ready = checks["database"].status == "ok"
    
    if is_ready:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """
    Liveness probe для Kubernetes/Docker
    Проверяет, что сервис работает
    """
    return {"status": "alive"}
