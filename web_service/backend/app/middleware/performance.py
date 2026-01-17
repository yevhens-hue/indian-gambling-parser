"""
Middleware для мониторинга производительности
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.utils.logger import logger
from app.services.metrics import get_metrics_service
from typing import Callable


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware для мониторинга производительности запросов
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        """
        Args:
            slow_request_threshold: Порог для медленных запросов в секундах
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с мониторингом производительности
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Записываем метрики
            metrics = get_metrics_service()
            metrics.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=process_time
            )
            
            # Логируем медленные запросы
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "duration": round(process_time, 3),
                        "threshold": self.slow_request_threshold,
                        "status_code": response.status_code,
                        "request_id": getattr(request.state, "request_id", None),
                    }
                )
            
            # Добавляем заголовок с временем обработки
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            
            # Записываем метрику ошибки
            metrics = get_metrics_service()
            metrics.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=process_time
            )
            
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": round(process_time, 3),
                    "error": str(e),
                    "request_id": getattr(request.state, "request_id", None),
                },
                exc_info=True
            )
            raise
