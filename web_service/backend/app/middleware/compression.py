"""
Middleware для сжатия ответов (Gzip)
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
from app.utils.logger import logger
import gzip
from io import BytesIO
from typing import Callable


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматического сжатия ответов
    Поддерживает Gzip compression для уменьшения размера ответов
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с добавлением compression
        """
        # Проверяем, поддерживает ли клиент gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        supports_gzip = "gzip" in accept_encoding
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Сжимаем только если:
        # 1. Клиент поддерживает gzip
        # 2. Ответ не уже сжат
        # 3. Размер ответа больше определенного порога (например, 1KB)
        # 4. Content-Type подходит для сжатия
        if supports_gzip and not response.headers.get("content-encoding"):
            content_type = response.headers.get("content-type", "")
            
            # Типы контента, которые стоит сжимать
            compressible_types = [
                "application/json",
                "application/javascript",
                "text/html",
                "text/css",
                "text/plain",
                "text/xml",
                "application/xml",
            ]
            
            should_compress = any(ct in content_type for ct in compressible_types)
            
            if should_compress:
                # Получаем тело ответа
                if hasattr(response, "body"):
                    body = response.body
                    
                    # Сжимаем только если размер больше 1KB
                    if len(body) > 1024:
                        compressed = gzip.compress(body)
                        
                        # Если сжатие эффективно (уменьшило размер)
                        if len(compressed) < len(body):
                            # Создаем новый response со сжатым содержимым
                            compressed_response = Response(
                                content=compressed,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type=response.media_type
                            )
                            compressed_response.headers["content-encoding"] = "gzip"
                            compressed_response.headers["content-length"] = str(len(compressed))
                            
                            logger.debug(
                                f"Response compressed: {len(body)} -> {len(compressed)} bytes",
                                extra={
                                    "path": request.url.path,
                                    "original_size": len(body),
                                    "compressed_size": len(compressed),
                                    "ratio": round(len(compressed) / len(body) * 100, 1)
                                }
                            )
                            
                            return compressed_response
        
        return response
