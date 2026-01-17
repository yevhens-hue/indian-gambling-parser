"""
Middleware для добавления Request ID к каждому запросу
Помогает отслеживать запросы в логах
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.utils.logger import logger
from typing import Callable


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления уникального ID к каждому запросу
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Добавляет request_id к запросу и ответу
        """
        # Генерируем уникальный ID для запроса
        request_id = str(uuid.uuid4())[:8]
        
        # Добавляем в state запроса
        request.state.request_id = request_id
        
        # Логируем начало запроса с ID
        logger.debug(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            }
        )
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            
            # Добавляем request_id в заголовки ответа
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # Логируем ошибку с request_id
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise
