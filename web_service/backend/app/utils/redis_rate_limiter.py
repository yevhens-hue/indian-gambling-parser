"""
Redis-based rate limiter для более эффективного rate limiting
"""
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis
import os
from app.utils.logger import logger


def get_redis_limiter() -> Optional[Limiter]:
    """
    Создает Limiter с Redis backend если Redis доступен
    
    Returns:
        Limiter с Redis backend или None если Redis недоступен
    """
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        # Пытаемся подключиться к Redis
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # Проверяем подключение
        redis_client.ping()
        
        logger.info("Redis rate limiter initialized successfully")
        
        # Создаем Limiter с Redis storage
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200/minute"],
            storage_uri=f"redis://{redis_host}:{redis_port}/{redis_db}"
        )
        
        return limiter
        
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        logger.warning(f"Redis недоступен для rate limiting, используется in-memory: {e}")
        return None


def get_limiter() -> Limiter:
    """
    Получить лучший доступный limiter (Redis или in-memory)
    """
    redis_limiter = get_redis_limiter()
    if redis_limiter:
        return redis_limiter
    
    # Fallback на in-memory limiter
    return Limiter(key_func=get_remote_address, default_limits=["200/minute"])
