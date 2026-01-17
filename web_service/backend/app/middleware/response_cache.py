"""
Middleware для кэширования ответов API
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.services.cache import get_cache_service
from app.utils.logger import logger
from typing import Callable
import hashlib
import json


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware для кэширования GET запросов
    """
    
    def __init__(self, app, cache_ttl: int = 300, cacheable_paths: list = None):
        """
        Args:
            cache_ttl: Время жизни кэша в секундах (по умолчанию 5 минут)
            cacheable_paths: Список путей для кэширования (None = все GET запросы)
        """
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_paths = cacheable_paths or []
    
    def _is_cacheable(self, request: Request) -> bool:
        """Проверяет, можно ли кэшировать запрос"""
        # Кэшируем только GET запросы
        if request.method != "GET":
            return False
        
        # Если указаны конкретные пути, проверяем их
        if self.cacheable_paths:
            return any(request.url.path.startswith(path) for path in self.cacheable_paths)
        
        # По умолчанию кэшируем все GET запросы (кроме health и metrics)
        excluded_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        return not any(request.url.path.startswith(path) for path in excluded_paths)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Генерирует ключ кэша на основе URL и query параметров"""
        # Создаем ключ из пути и query параметров
        cache_data = {
            "path": request.url.path,
            "query": dict(request.query_params)
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        # MD5 используется только для генерации ключа кэша, не для криптографии
        cache_hash = hashlib.md5(cache_string.encode(), usedforsecurity=False).hexdigest()
        return f"response_cache:{cache_hash}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с кэшированием
        """
        # Проверяем, можно ли кэшировать
        if not self._is_cacheable(request):
            return await call_next(request)
        
        cache_service = get_cache_service()
        
        # Генерируем ключ кэша
        cache_key = self._generate_cache_key(request)
        
        # Пытаемся получить из кэша
        cached_response = cache_service.get(cache_key)
        if cached_response:
            logger.debug(
                f"Cache hit for {request.url.path}",
                extra={
                    "cache_key": cache_key,
                    "path": request.url.path,
                }
            )
            # Возвращаем кэшированный ответ
            from starlette.responses import JSONResponse
            return JSONResponse(
                content=cached_response,
                headers={"X-Cache": "HIT", "X-Cache-Key": cache_key}
            )
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Добавляем заголовок с ключом кэша для отладки
        response.headers["X-Cache-Key"] = cache_key
        
        # Проверяем, доступен ли кэш
        if not cache_service.enabled:
            response.headers["X-Cache"] = "DISABLED"
            return response
        
        # Кэшируем только успешные ответы
        if response.status_code == 200:
            try:
                # Получаем тело ответа
                if hasattr(response, "body"):
                    body = response.body
                    # Парсим JSON если возможно
                    try:
                        import json
                        response_data = json.loads(body.decode())
                        # Сохраняем в кэш
                        if cache_service.set(cache_key, response_data, ttl=self.cache_ttl):
                            logger.debug(
                                f"Cache set for {request.url.path}",
                                extra={
                                    "cache_key": cache_key,
                                    "path": request.url.path,
                                    "ttl": self.cache_ttl,
                                }
                            )
                            response.headers["X-Cache"] = "MISS"
                        else:
                            response.headers["X-Cache"] = "DISABLED"
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Не JSON ответ, не кэшируем
                        response.headers["X-Cache"] = "SKIP"
            except Exception as e:
                logger.warning(
                    f"Failed to cache response for {request.url.path}",
                    extra={"error": str(e)},
                    exc_info=True
                )
                response.headers["X-Cache"] = "ERROR"
        else:
            response.headers["X-Cache"] = "SKIP"
        
        return response
