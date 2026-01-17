"""
API endpoints для статистики кэша
"""
from fastapi import APIRouter
from app.utils.redis_optimizer import get_redis_optimizer
from app.utils.logger import logger

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats():
    """
    Получить статистику Redis кэша
    
    Returns:
        Статистика использования кэша
    """
    try:
        optimizer = get_redis_optimizer()
        stats = optimizer.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        return {
            "enabled": False,
            "error": str(e)
        }


@router.post("/clear")
async def clear_cache(pattern: str = "*"):
    """
    Очистить кэш по паттерну
    
    Args:
        pattern: Паттерн для очистки (по умолчанию все)
        
    Returns:
        Количество удаленных ключей
    """
    try:
        optimizer = get_redis_optimizer()
        count = optimizer.invalidate_pattern(pattern)
        return {
            "success": True,
            "deleted_count": count,
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
