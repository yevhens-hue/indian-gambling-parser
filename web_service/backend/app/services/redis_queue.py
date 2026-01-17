"""
Простая очередь задач на основе Redis
"""
import json
import time
from typing import Optional, Callable, Any, Dict
from app.services.cache import get_cache_service
from app.utils.logger import logger


class RedisQueue:
    """
    Простая очередь задач на основе Redis LIST
    """
    
    def __init__(self, queue_name: str = "default"):
        """
        Args:
            queue_name: Имя очереди
        """
        self.queue_name = f"queue:{queue_name}"
        self.cache_service = get_cache_service()
    
    def enqueue(self, task_data: Dict[str, Any], priority: int = 0) -> bool:
        """
        Добавить задачу в очередь
        
        Args:
            task_data: Данные задачи
            priority: Приоритет (чем выше, тем раньше выполнится)
        
        Returns:
            True если успешно
        """
        if not self.cache_service.is_enabled():
            logger.warning("Redis not available, task not queued")
            return False
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return False
        
        try:
            task = {
                "data": task_data,
                "priority": priority,
                "timestamp": time.time(),
                "id": f"{int(time.time() * 1000)}"
            }
            
            task_json = json.dumps(task, ensure_ascii=False)
            
            # Используем sorted set для приоритетной очереди
            score = priority * 1000000 + time.time()  # Приоритет + timestamp
            redis_client.zadd(self.queue_name, {task_json: score})
            
            logger.debug(f"Task enqueued: {self.queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueueing task: {e}", exc_info=True)
            return False
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Получить задачу из очереди
        
        Args:
            timeout: Максимальное время ожидания (None = без ожидания)
        
        Returns:
            Данные задачи или None
        """
        if not self.cache_service.is_enabled():
            return None
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return None
        
        try:
            # Получаем задачу с наивысшим приоритетом
            result = redis_client.zpopmax(self.queue_name, 1)
            
            if result and len(result) > 0:
                task_json = result[0]
                task = json.loads(task_json)
                logger.debug(f"Task dequeued: {self.queue_name}")
                return task.get("data")
            
            return None
            
        except Exception as e:
            logger.error(f"Error dequeuing task: {e}", exc_info=True)
            return None
    
    def size(self) -> int:
        """Получить размер очереди"""
        if not self.cache_service.is_enabled():
            return 0
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return 0
        
        try:
            return redis_client.zcard(self.queue_name)
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0
    
    def clear(self) -> bool:
        """Очистить очередь"""
        if not self.cache_service.is_enabled():
            return False
        
        redis_client = self.cache_service.redis_client
        if not redis_client:
            return False
        
        try:
            redis_client.delete(self.queue_name)
            return True
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
            return False


def get_queue(queue_name: str = "default") -> RedisQueue:
    """Получить очередь по имени"""
    return RedisQueue(queue_name)
