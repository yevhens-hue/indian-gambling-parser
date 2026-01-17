"""
Middleware для добавления security headers
"""
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления security headers к ответам
    Расширенная версия с поддержкой HSTS, CSP и других современных заголовков
    """
    
    def __init__(self, app, strict_transport_security: bool = True):
        """
        Args:
            app: FastAPI приложение
            strict_transport_security: Включить HSTS (Strict-Transport-Security)
        """
        super().__init__(app)
        self.strict_transport_security = strict_transport_security
        self.environment = os.getenv("ENVIRONMENT", "production")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Добавляет security headers к ответу
        """
        response = await call_next(request)
        
        # Базовые security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
        }
        
        # HSTS (только для HTTPS в production)
        if self.strict_transport_security and self.environment == "production":
            security_headers["Strict-Transport-Security"] = (
                "max-age=31536000; "
                "includeSubDomains; "
                "preload"
            )
        
        # Content Security Policy
        if self.environment == "production":
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
        else:
            # Более мягкая CSP для development
            security_headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss: http: https:;"
            )
        
        # X-DNS-Prefetch-Control
        security_headers["X-DNS-Prefetch-Control"] = "off"
        
        # Expect-CT (для дополнительной безопасности сертификатов)
        if self.environment == "production":
            security_headers["Expect-CT"] = (
                "max-age=86400, "
                "enforce"
            )
        
        # Добавляем headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
