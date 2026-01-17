"""
Middleware для фильтрации IP адресов
"""
import os
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable, Set, Optional
from app.utils.logger import logger


class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    Middleware для фильтрации запросов по IP адресам
    Поддерживает whitelist и blacklist
    """
    
    def __init__(
        self,
        app,
        whitelist: Optional[Set[str]] = None,
        blacklist: Optional[Set[str]] = None,
        enabled: bool = True
    ):
        """
        Args:
            app: FastAPI приложение
            whitelist: Множество разрешенных IP адресов (если задано, только эти IP разрешены)
            blacklist: Множество заблокированных IP адресов
            enabled: Включить фильтрацию (можно отключить через переменную окружения)
        """
        super().__init__(app)
        
        # Загружаем из переменных окружения, если не переданы
        self.enabled = os.getenv("IP_FILTER_ENABLED", str(enabled)).lower() == "true"
        
        # Whitelist из переменных окружения (через запятую)
        env_whitelist = os.getenv("IP_WHITELIST", "")
        if env_whitelist:
            self.whitelist = set(ip.strip() for ip in env_whitelist.split(",") if ip.strip())
        else:
            self.whitelist = whitelist or set()
        
        # Blacklist из переменных окружения (через запятую)
        env_blacklist = os.getenv("IP_BLACKLIST", "")
        if env_blacklist:
            self.blacklist = set(ip.strip() for ip in env_blacklist.split(",") if ip.strip())
        else:
            self.blacklist = blacklist or set()
        
        # Пути, которые не требуют проверки IP (например, health checks)
        self.excluded_paths = {
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
        }
    
    def get_client_ip(self, request: Request) -> str:
        """
        Получить реальный IP адрес клиента
        
        Args:
            request: HTTP запрос
            
        Returns:
            IP адрес клиента
        """
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Берем первый IP из списка
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback на client.host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def is_ip_allowed(self, ip: str) -> bool:
        """
        Проверить, разрешен ли IP адрес
        
        Args:
            ip: IP адрес для проверки
            
        Returns:
            True если IP разрешен
        """
        # Проверяем blacklist
        if self.blacklist and ip in self.blacklist:
            logger.warning(f"IP {ip} is in blacklist")
            return False
        
        # Если whitelist задан, проверяем его
        if self.whitelist:
            if ip not in self.whitelist:
                logger.warning(f"IP {ip} is not in whitelist")
                return False
        
        return True
    
    def is_path_excluded(self, path: str) -> bool:
        """
        Проверить, исключен ли путь из проверки
        
        Args:
            path: Путь запроса
            
        Returns:
            True если путь исключен
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с фильтрацией IP
        """
        if not self.enabled:
            return await call_next(request)
        
        # Пропускаем исключенные пути
        if self.is_path_excluded(request.url.path):
            return await call_next(request)
        
        client_ip = self.get_client_ip(request)
        
        # Проверяем IP
        if not self.is_ip_allowed(client_ip):
            logger.warning(
                "IP filter: Access denied",
                extra={
                    "ip": client_ip,
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return await call_next(request)
