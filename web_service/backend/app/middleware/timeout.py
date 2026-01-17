"""
Middleware для установки timeout на запросы
"""
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.utils.logger import logger
from typing import Callable


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware для установки максимального времени выполнения запроса
    """
    
    def __init__(self, app, timeout: float = 30.0):
        """
        Args:
            timeout: Максимальное время выполнения запроса в секундах
        """
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Обработка запроса с timeout
        """
        try:
            # Выполняем запрос с timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout for {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "timeout": self.timeout,
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "detail": f"Request exceeded maximum time of {self.timeout} seconds",
                    "path": request.url.path
                }
            )
