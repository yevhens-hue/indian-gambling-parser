"""
Distributed locking через Redis
"""
import time
import uuid
from typing import Optional
from app.services.cache import get_cache_service
from app.utils.logger import logger


class RedisLock:
    """
    Distributed lock на основе Redis
    """
    
    def __init__(self, key: str, timeout: float = 10.0, retry_delay: float = 0.1):
        """
        Args:
            key: Ключ блокировки
            timeout: Время жизни блокировки в секундах
            retry_delay: Задержка между попытками получения блокировки
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.cache_service = get_cache_service()
        self.lock_value: Optional[str] = None
    
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Получить блокировку
        
        Args:
            blocking: Блокировать ли до получения блокировки
            timeout: Максимальное время ожидания (None = бесконечно)
        
        Returns:
            True если блокировка получена
        """
        if not self.cache_service.is_enabled():
            logger.warning("Redis not available, lock acquisition skipped")
            return True  # Разрешаем выполнение если Redis недоступен
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return True
        
        # Генерируем уникальное значение для блокировки
        self.lock_value = str(uuid.uuid4())
        start_time = time.time()
        
        while True:
            try:
                # Пытаемся установить блокировку с NX (только если не существует)
                # и EX (expiration time)
                result = redis_client.set(
                    self.key,
                    self.lock_value,
                    nx=True,
                    ex=int(self.timeout)
                )
                
                if result:
                    logger.debug(f"Lock acquired: {self.key}")
                    return True
                
                # Если не blocking, сразу возвращаем False
                if not blocking:
                    return False
                
                # Проверяем timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.debug(f"Lock acquisition timeout: {self.key}")
                        return False
                
                # Ждем перед следующей попыткой
                time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Error acquiring lock {self.key}: {e}", exc_info=True)
                return False
    
    def release(self) -> bool:
        """
        Освободить блокировку
        
        Returns:
            True если блокировка успешно освобождена
        """
        if not self.cache_service.is_enabled() or not self.lock_value:
            return True
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return True
        
        try:
            # Lua script для атомарного удаления только если значение совпадает
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = redis_client.eval(lua_script, 1, self.key, self.lock_value)
            
            if result:
                logger.debug(f"Lock released: {self.key}")
                return True
            else:
                logger.warning(f"Lock release failed (value mismatch or expired): {self.key}")
                return False
                
        except Exception as e:
            logger.error(f"Error releasing lock {self.key}: {e}", exc_info=True)
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False


def acquire_lock(key: str, timeout: float = 10.0) -> RedisLock:
    """
    Удобная функция для получения блокировки
    
    Пример:
        with acquire_lock("import_data"):
            # Критическая секция
            pass
    """
    return RedisLock(key, timeout=timeout)
