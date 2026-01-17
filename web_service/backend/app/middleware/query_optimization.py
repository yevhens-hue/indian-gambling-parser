"""
Middleware для оптимизации запросов к базе данных
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.utils.logger import logger
from app.services.metrics import get_metrics_service


class QueryOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware для мониторинга и оптимизации запросов к БД
    """
    
    def __init__(self, app, slow_query_threshold: float = 1.0):
        """
        Args:
            app: FastAPI приложение
            slow_query_threshold: Порог для медленных запросов в секундах
        """
        super().__init__(app)
        self.slow_query_threshold = slow_query_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с мониторингом производительности БД
        """
        # Этот middleware в основном для логирования и метрик
        # Реальная оптимизация происходит в StorageAdapter
        
        response = await call_next(request)
        
        # Проверяем заголовок с информацией о времени выполнения БД запросов
        # (если такой заголовок был добавлен в обработчике)
        db_time_header = response.headers.get("X-DB-Query-Time")
        if db_time_header:
            try:
                db_time = float(db_time_header)
                if db_time > self.slow_query_threshold:
                    logger.warning(
                        "Slow database query detected",
                        extra={
                            "path": request.url.path,
                            "method": request.method,
                            "db_time": db_time,
                            "threshold": self.slow_query_threshold,
                            "request_id": getattr(request.state, "request_id", None),
                        }
                    )
            except ValueError:
                pass
        
        return response
