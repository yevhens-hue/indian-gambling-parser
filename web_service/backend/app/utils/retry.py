"""
Утилиты для retry механизма
"""
import asyncio
import time
from typing import Callable, TypeVar, Optional, List
from functools import wraps
from app.utils.logger import logger

T = TypeVar('T')


class RetryError(Exception):
    """Исключение при исчерпании попыток retry"""
    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Декоратор для retry механизма
    
    Args:
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками (в секундах)
        backoff: Множитель для увеличения задержки
        exceptions: Кортеж исключений, при которых нужно повторять попытку
        on_retry: Функция, вызываемая при каждой попытке retry
    
    Пример:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError, TimeoutError))
        async def fetch_data():
            # ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "exception": str(e),
                                "exception_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        raise RetryError(f"Failed after {max_attempts} attempts: {str(e)}") from e
                    
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts} for {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "exception": str(e),
                            "exception_type": type(e).__name__
                        }
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, max_attempts, e)
                        except Exception:
                            pass
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # Не должно достигнуть этой точки, но на всякий случай
            raise RetryError(f"Failed after {max_attempts} attempts") from last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "exception": str(e),
                                "exception_type": type(e).__name__
                            },
                            exc_info=True
                        )
                        raise RetryError(f"Failed after {max_attempts} attempts: {str(e)}") from e
                    
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts} for {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "exception": str(e),
                            "exception_type": type(e).__name__
                        }
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, max_attempts, e)
                        except Exception:
                            pass
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise RetryError(f"Failed after {max_attempts} attempts") from last_exception
        
        # Определяем, какая версия нужна
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
