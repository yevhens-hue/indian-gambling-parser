"""
Утилиты для оптимизации работы с Redis
"""
from typing import Any, Optional, List, Dict
from app.services.cache import get_cache_service
from app.utils.logger import logger
import json
import hashlib


class RedisOptimizer:
    """
    Класс для оптимизации работы с Redis
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        Пакетное получение значений из Redis
        
        Args:
            keys: Список ключей для получения
            
        Returns:
            Словарь {key: value} для найденных ключей
        """
        if not self.cache_service.enabled:
            return {}
        
        try:
            redis_client = self.cache_service.redis_client
            if not redis_client:
                return {}
            
            # Используем mget для пакетного получения
            values = redis_client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            
            return result
        except Exception as e:
            logger.warning(f"Batch get failed: {e}", exc_info=True)
            return {}
    
    def batch_set(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        Пакетное сохранение значений в Redis
        
        Args:
            items: Словарь {key: value} для сохранения
            ttl: TTL в секундах
            
        Returns:
            Количество успешно сохраненных ключей
        """
        if not self.cache_service.enabled:
            return 0
        
        try:
            redis_client = self.cache_service.redis_client
            if not redis_client:
                return 0
            
            if ttl is None:
                ttl = self.cache_service.default_ttl
            
            # Используем pipeline для пакетной записи
            pipe = redis_client.pipeline()
            
            for key, value in items.items():
                try:
                    value_json = json.dumps(value, ensure_ascii=False, default=str)
                    pipe.setex(key, ttl, value_json)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to serialize {key}: {e}")
            
            pipe.execute()
            return len(items)
        except Exception as e:
            logger.warning(f"Batch set failed: {e}", exc_info=True)
            return 0
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Инвалидация всех ключей по паттерну
        
        Args:
            pattern: Паттерн для поиска (например, "providers:*")
            
        Returns:
            Количество удаленных ключей
        """
        return self.cache_service.clear_pattern(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша
        
        Returns:
            Словарь со статистикой
        """
        if not self.cache_service.enabled:
            return {
                "enabled": False,
                "message": "Redis not available"
            }
        
        try:
            redis_client = self.cache_service.redis_client
            if not redis_client:
                return {"enabled": False}
            
            info = redis_client.info()
            
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": redis_client.dbsize(),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}", exc_info=True)
            return {"enabled": False, "error": str(e)}


# Глобальный экземпляр
_redis_optimizer: Optional[RedisOptimizer] = None


def get_redis_optimizer() -> RedisOptimizer:
    """Получить глобальный экземпляр RedisOptimizer"""
    global _redis_optimizer
    
    if _redis_optimizer is None:
        _redis_optimizer = RedisOptimizer()
    
    return _redis_optimizer
