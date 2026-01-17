"""
Middleware для санитизации и валидации входных данных
"""
import re
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.utils.logger import logger


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware для санитизации входных данных и защиты от инъекций
    """
    
    # Паттерны для обнаружения потенциально опасных входных данных
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table)",
        r"(?i)(or\s+1\s*=\s*1|or\s+'1'\s*=\s*'1')",
        r"(?i)(exec\s*\(|execute\s*\(|sp_executesql)",
        r"(?i)(--|\#|\/\*|\*\/)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # onclick=, onerror=, etc.
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB по умолчанию
        """
        Args:
            max_request_size: Максимальный размер запроса в байтах
        """
        super().__init__(app)
        self.max_request_size = max_request_size
    
    def sanitize_string(self, value: str) -> str:
        """
        Санитизация строки от потенциально опасных символов
        
        Args:
            value: Входная строка
            
        Returns:
            Санитизированная строка
        """
        if not isinstance(value, str):
            return value
        
        # Удаляем нулевые байты
        value = value.replace('\x00', '')
        
        # Удаляем управляющие символы (кроме табуляции и новой строки)
        value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', value)
        
        return value
    
    def check_patterns(self, value: str, patterns: list, pattern_name: str) -> bool:
        """
        Проверка строки на наличие опасных паттернов
        
        Args:
            value: Строка для проверки
            patterns: Список регулярных выражений
            pattern_name: Название типа паттерна (для логирования)
            
        Returns:
            True если найдено совпадение
        """
        if not isinstance(value, str):
            return False
        
        for pattern in patterns:
            if re.search(pattern, value):
                logger.warning(
                    f"Potential {pattern_name} detected",
                    extra={
                        "pattern": pattern,
                        "value_preview": value[:100],
                        "pattern_name": pattern_name
                    }
                )
                return True
        return False
    
    def sanitize_dict(self, data: dict) -> dict:
        """
        Рекурсивная санитизация словаря
        
        Args:
            data: Словарь для санитизации
            
        Returns:
            Санитизированный словарь
        """
        sanitized = {}
        for key, value in data.items():
            # Санитизируем ключ
            sanitized_key = self.sanitize_string(str(key))
            
            if isinstance(value, dict):
                sanitized[sanitized_key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[sanitized_key] = [
                    self.sanitize_dict(item) if isinstance(item, dict)
                    else self.sanitize_string(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Проверяем на опасные паттерны
                if self.check_patterns(value, self.SQL_INJECTION_PATTERNS, "SQL injection"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: potential SQL injection detected"
                    )
                
                if self.check_patterns(value, self.XSS_PATTERNS, "XSS"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: potential XSS detected"
                    )
                
                if self.check_patterns(value, self.PATH_TRAVERSAL_PATTERNS, "Path traversal"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: potential path traversal detected"
                    )
                
                sanitized[sanitized_key] = self.sanitize_string(value)
            else:
                sanitized[sanitized_key] = value
        
        return sanitized
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обработка запроса с санитизацией входных данных
        """
        # Проверяем размер запроса
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Maximum size: {self.max_request_size / 1024 / 1024:.1f}MB"
                    )
            except ValueError:
                pass
        
        # Санитизируем query параметры
        if request.query_params:
            try:
                query_dict = dict(request.query_params)
                sanitized_query = self.sanitize_dict(query_dict)
                # Обновляем query params (если нужно)
                # В FastAPI query params уже обработаны, но мы можем проверить их
                for key, value in sanitized_query.items():
                    if isinstance(value, str):
                        if self.check_patterns(value, self.SQL_INJECTION_PATTERNS, "SQL injection"):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid query parameter"
                            )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Error sanitizing query params: {e}")
        
        # Санитизируем path параметры
        if request.path_params:
            for key, value in request.path_params.items():
                if isinstance(value, str):
                    if self.check_patterns(value, self.PATH_TRAVERSAL_PATTERNS, "Path traversal"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid path parameter"
                        )
        
        response = await call_next(request)
        return response
