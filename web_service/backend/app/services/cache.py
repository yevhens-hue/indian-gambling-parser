"""Сервис кэширования с Redis"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import os

# Redis опционален
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheService:
    """Сервис кэширования с Redis"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        Инициализация cache service
        
        Args:
            redis_url: URL Redis (например, "redis://localhost:6379/0")
                     Если None, пытается подключиться к localhost:6379
            default_ttl: TTL по умолчанию в секундах (5 минут)
        """
        self.redis_client = None
        self.default_ttl = default_ttl
        self.enabled = False
        
        if not REDIS_AVAILABLE:
            return
        
        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # Пытаемся подключиться к localhost
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                redis_db = int(os.getenv("REDIS_DB", "0"))
                
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
            
            # Проверяем подключение
            self.redis_client.ping()
            self.enabled = True
            
        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            # Redis недоступен, работаем без кэша
            self.redis_client = None
            self.enabled = False
            try:
                from app.utils.logger import logger
                logger.warning(f"Redis недоступен, кэширование отключено: {e}")
            except ImportError:
                print(f"⚠️  Redis недоступен, кэширование отключено: {e}")
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Создание ключа кэша из аргументов"""
        # Создаем строковое представление аргументов
        key_parts = [prefix]
        
        # Добавляем позиционные аргументы
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(str(arg).encode(), usedforsecurity=False).hexdigest()[:8])
        
        # Добавляем именованные аргументы (отсортированные)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")
                else:
                    key_parts.append(f"{k}:{hashlib.md5(str(v).encode(), usedforsecurity=False).hexdigest()[:8]}")
        
        key_string = ":".join(key_parts)
        # Ограничиваем длину ключа (Redis limit ~512MB, но для читаемости ограничиваем)
        if len(key_string) > 250:
            key_string = key_string[:200] + ":" + hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()
        
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получить значение из кэша
        
        Args:
            key: Ключ кэша
        
        Returns:
            Значение или None если не найдено
        """
        if not self.enabled or not self.redis_client:
            # Записываем метрику промаха кэша
            try:
                from app.services.metrics import get_metrics_service
                prefix = key.split(':')[0] if ':' in key else 'unknown'
                get_metrics_service().record_cache_miss(prefix)
            except:
                pass
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Записываем метрику попадания в кэш
                try:
                    from app.services.metrics import get_metrics_service
                    prefix = key.split(':')[0] if ':' in key else 'unknown'
                    get_metrics_service().record_cache_hit(prefix)
                except:
                    pass
                return json.loads(value)
            else:
                # Записываем метрику промаха кэша
                try:
                    from app.services.metrics import get_metrics_service
                    prefix = key.split(':')[0] if ':' in key else 'unknown'
                    get_metrics_service().record_cache_miss(prefix)
                except:
                    pass
        except (json.JSONDecodeError, redis.RedisError, Exception) as e:
            try:
                from app.utils.logger import logger
                logger.warning(f"Ошибка при получении из кэша {key}: {e}")
            except ImportError:
                pass
            return None
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Сохранить значение в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для сохранения
            ttl: TTL в секундах (если None, используется default_ttl)
        
        Returns:
            True если успешно, False иначе
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            value_json = json.dumps(value, ensure_ascii=False, default=str)
            self.redis_client.setex(key, ttl, value_json)
            return True
        except (TypeError, redis.RedisError, Exception) as e:
            try:
                from app.utils.logger import logger
                logger.warning(f"Ошибка при сохранении в кэш {key}: {e}")
            except ImportError:
                pass
            return False
    
    def delete(self, key: str) -> bool:
        """Удалить ключ из кэша"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except redis.RedisError:
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Удалить все ключи по паттерну
        
        Args:
            pattern: Паттерн (например, "providers:*")
        
        Returns:
            Количество удаленных ключей
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0
    
    def get_or_set(self, key: str, func: Callable, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """
        Получить из кэша или выполнить функцию и сохранить результат
        
        Args:
            key: Ключ кэша
            func: Функция для выполнения если кэш пуст
            ttl: TTL в секундах
            *args, **kwargs: Аргументы для функции
        
        Returns:
            Результат функции (из кэша или новый)
        """
        # Пытаемся получить из кэша
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Выполняем функцию
        result = func(*args, **kwargs)
        
        # Сохраняем в кэш
        self.set(key, result, ttl)
        
        return result
    
    def invalidate_providers(self):
        """Инвалидировать все кэши связанные с провайдерами"""
        return self.clear_pattern("providers:*")
    
    def invalidate_statistics(self):
        """Инвалидировать кэш статистики"""
        return self.delete("statistics:all") + self.clear_pattern("statistics:*")


# Глобальный экземпляр cache service
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Получить глобальный cache service (singleton)"""
    global _cache_service
    
    if _cache_service is None:
        redis_url = os.getenv("REDIS_URL")
        default_ttl = int(os.getenv("CACHE_TTL", "300"))  # 5 минут по умолчанию
        _cache_service = CacheService(redis_url=redis_url, default_ttl=default_ttl)
    
    return _cache_service


def cached(prefix: str = "cache", ttl: int = 300):
    """
    Декоратор для кэширования результатов функции
    
    Args:
        prefix: Префикс для ключа кэша
        ttl: TTL в секундах
    
    Пример:
        @cached(prefix="providers", ttl=300)
        def get_providers(merchant=None):
            # ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Создаем ключ из имени функции и аргументов
            key = cache._make_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


async def async_cached(prefix: str = "cache", ttl: int = 300):
    """Асинхронная версия декоратора кэширования"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Создаем ключ
            key = cache._make_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
