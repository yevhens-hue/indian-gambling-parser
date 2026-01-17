"""
API endpoints для мониторинга и диагностики
"""
from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime, timedelta
from app.utils.logger import logger
from app.services.metrics import get_metrics_service
from app.services.cache import get_cache_service
from app.services.storage_adapter import StorageAdapter

router = APIRouter(tags=["monitoring"])


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Получить общий статус системы
    
    Returns:
        Словарь со статусом всех компонентов
    """
    status_info = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "ok",
        "components": {}
    }
    
    # Проверка базы данных
    try:
        storage = StorageAdapter()
        result = storage.get_all_providers(limit=1)
        status_info["components"]["database"] = {
            "status": "ok",
            "total_providers": result.get("total", 0)
        }
    except Exception as e:
        status_info["components"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        status_info["status"] = "degraded"
    
    # Проверка кэша
    try:
        cache_service = get_cache_service()
        status_info["components"]["cache"] = {
            "status": "ok" if cache_service.enabled else "disabled",
            "enabled": cache_service.enabled
        }
    except Exception as e:
        status_info["components"]["cache"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Проверка метрик
    try:
        metrics = get_metrics_service()
        status_info["components"]["metrics"] = {
            "status": "ok" if metrics.enabled else "disabled",
            "enabled": metrics.enabled
        }
    except Exception as e:
        status_info["components"]["metrics"] = {
            "status": "error",
            "error": str(e)
        }
    
    return status_info


@router.get("/metrics/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Получить краткую сводку метрик
    
    Returns:
        Сводка метрик производительности
    """
    try:
        metrics = get_metrics_service()
        
        # Если Prometheus не доступен, возвращаем базовую информацию
        if not metrics.enabled:
            return {
                "enabled": False,
                "message": "Prometheus metrics not available"
            }
        
        # Здесь можно добавить логику для получения сводки метрик
        # из Prometheus registry, если нужно
        
        return {
            "enabled": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": "Metrics are being collected. Use /metrics endpoint for Prometheus format."
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}", exc_info=True)
        return {
            "enabled": False,
            "error": str(e)
        }


@router.get("/performance")
async def get_performance_info() -> Dict[str, Any]:
    """
    Получить информацию о производительности системы
    
    Returns:
        Информация о производительности
    """
    performance_info = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    # Информация о системе (если доступна)
    try:
        import psutil
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        performance_info["system"] = {
            "memory": {
                "total_gb": round(memory.total / (1024 ** 3), 2),
                "available_gb": round(memory.available / (1024 ** 3), 2),
                "used_percent": round(memory.percent, 1)
            },
            "cpu": {
                "usage_percent": round(cpu_percent, 1)
            }
        }
    except ImportError:
        performance_info["system"] = {
            "message": "psutil not installed"
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}", exc_info=True)
        performance_info["system"] = {
            "error": str(e)
        }
    
    # Информация о кэше
    try:
        cache_service = get_cache_service()
        if cache_service.enabled:
            # Можно добавить статистику кэша, если доступна
            performance_info["cache"] = {
                "enabled": True,
                "status": "ok"
            }
        else:
            performance_info["cache"] = {
                "enabled": False
            }
    except Exception as e:
        performance_info["cache"] = {
            "error": str(e)
        }
    
    return performance_info
