"""
Redis-based rate limiter для распределенного rate limiting
"""
import time
from typing import Optional
from app.services.cache import get_cache_service
from app.utils.logger import logger


class RedisRateLimiter:
    """
    Rate limiter на основе Redis для распределенного rate limiting
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: Optional[str] = None
    ) -> tuple[bool, dict]:
        """
        Проверяет, разрешен ли запрос
        
        Args:
            key: Ключ для rate limiting (например, IP адрес или user_id)
            limit: Максимальное количество запросов
            window: Временное окно в секундах
            identifier: Дополнительный идентификатор (например, endpoint)
        
        Returns:
            Tuple (is_allowed, info_dict)
            info_dict содержит:
                - allowed: bool
                - remaining: int - оставшиеся запросы
                - reset_time: float - время сброса
                - limit: int
        """
        if not self.cache_service.is_enabled():
            # Если Redis недоступен, разрешаем все запросы
            return True, {
                "allowed": True,
                "remaining": limit,
                "reset_time": time.time() + window,
                "limit": limit
            }
        
        # Создаем ключ для Redis
        redis_key = f"rate_limit:{key}"
        if identifier:
            redis_key += f":{identifier}"
        
        try:
            redis_client = self.cache_service.redis_client
            if not redis_client:
                return True, {"allowed": True, "remaining": limit, "limit": limit}
            
            # Используем Redis INCR с TTL
            current = redis_client.incr(redis_key)
            
            # Устанавливаем TTL при первом запросе
            if current == 1:
                redis_client.expire(redis_key, window)
            
            # Проверяем лимит
            ttl = redis_client.ttl(redis_key)
            remaining = max(0, limit - current)
            allowed = current <= limit
            
            return allowed, {
                "allowed": allowed,
                "remaining": remaining,
                "reset_time": time.time() + (ttl if ttl > 0 else window),
                "limit": limit,
                "current": current
            }
        except Exception as e:
            logger.warning(f"Redis rate limiter error: {e}", exc_info=True)
            # При ошибке разрешаем запрос
            return True, {
                "allowed": True,
                "remaining": limit,
                "limit": limit,
                "error": str(e)
            }
    
    def reset(self, key: str, identifier: Optional[str] = None) -> bool:
        """
        Сбрасывает счетчик для ключа
        
        Args:
            key: Ключ для сброса
            identifier: Дополнительный идентификатор
        
        Returns:
            True если успешно
        """
        if not self.cache_service.is_enabled():
            return False
        
        redis_key = f"rate_limit:{key}"
        if identifier:
            redis_key += f":{identifier}"
        
        try:
            redis_client = self.cache_service.redis_client
            if redis_client:
                redis_client.delete(redis_key)
                return True
        except Exception as e:
            logger.warning(f"Redis rate limiter reset error: {e}")
        
        return False


# Глобальный экземпляр
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_redis_rate_limiter() -> RedisRateLimiter:
    """Получить глобальный Redis rate limiter"""
    global _redis_rate_limiter
    if _redis_rate_limiter is None:
        _redis_rate_limiter = RedisRateLimiter()
    return _redis_rate_limiter
