"""
Middleware для аудита безопасности
"""
import json
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.utils.logger import logger


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования событий безопасности
    """
    
    # Пути, которые требуют особого внимания с точки зрения безопасности
    SENSITIVE_PATHS = [
        "/api/auth/login",
        "/api/auth/token",
        "/api/providers",
        "/api/export",
        "/api/import",
    ]
    
    # HTTP методы, которые изменяют данные
    MODIFYING_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    
    def __init__(self, app, log_all_requests: bool = False):
        """
        Args:
            log_all_requests: Логировать все запросы (по умолчанию только важные)
        """
        super().__init__(app)
        self.log_all_requests = log_all_requests
    
    def should_log(self, request: Request) -> bool:
        """
        Определить, нужно ли логировать запрос
        
        Args:
            request: HTTP запрос
            
        Returns:
            True если нужно логировать
        """
        if self.log_all_requests:
            return True
        
        # Логируем модифицирующие запросы
        if request.method in self.MODIFYING_METHODS:
            return True
        
        # Логируем запросы к чувствительным путям
        if any(request.url.path.startswith(path) for path in self.SENSITIVE_PATHS):
            return True
        
        return False
    
    def get_client_info(self, request: Request) -> dict:
        """
        Получить информацию о клиенте
        
        Args:
            request: HTTP запрос
            
        Returns:
            Словарь с информацией о клиенте
        """
        client_host = request.client.host if request.client else None
        
        # Получаем реальный IP из заголовков (если за прокси)
        real_ip = (
            request.headers.get("X-Real-IP") or
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            client_host
        )
        
        return {
            "ip": real_ip,
            "user_agent": request.headers.get("user-agent", "Unknown"),
            "referer": request.headers.get("referer"),
            "origin": request.headers.get("origin"),
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с аудитом безопасности
        """
        if not self.should_log(request):
            return await call_next(request)
        
        client_info = self.get_client_info(request)
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # Логируем успешный запрос
            logger.info(
                "Security audit: Request completed",
                extra={
                    "event_type": "request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client": client_info,
                    "timestamp": start_time.isoformat() + "Z",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
            # Логируем подозрительные ответы (4xx, 5xx)
            if response.status_code >= 400:
                logger.warning(
                    "Security audit: Error response",
                    extra={
                        "event_type": "error_response",
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "client": client_info,
                        "timestamp": start_time.isoformat() + "Z",
                        "request_id": getattr(request.state, "request_id", None),
                    }
                )
            
            return response
            
        except Exception as e:
            # Логируем исключения
            logger.error(
                "Security audit: Request failed with exception",
                extra={
                    "event_type": "request_exception",
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "client": client_info,
                    "timestamp": start_time.isoformat() + "Z",
                    "request_id": getattr(request.state, "request_id", None),
                },
                exc_info=True
            )
            raise
