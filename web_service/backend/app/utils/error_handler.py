"""
Улучшенная обработка ошибок и логирование
"""
import traceback
import sys
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.utils.logger import logger
from app.utils.structured_logging import get_logger


class ErrorHandler:
    """
    Класс для централизованной обработки ошибок
    """
    
    def __init__(self, include_traceback: bool = False):
        """
        Args:
            include_traceback: Включать traceback в ответы (только для development)
        """
        self.include_traceback = include_traceback
        self.structured_logger = get_logger()
    
    def handle_exception(
        self,
        request: Request,
        exc: Exception,
        status_code: int = 500,
        detail: Optional[str] = None
    ) -> JSONResponse:
        """
        Обработать исключение
        
        Args:
            request: HTTP запрос
            exc: Исключение
            status_code: HTTP статус код
            detail: Детали ошибки
            
        Returns:
            JSONResponse с информацией об ошибке
        """
        error_id = getattr(request.state, "request_id", None) or "unknown"
        error_type = type(exc).__name__
        error_message = str(exc) or detail or "Internal server error"
        
        # Логируем ошибку структурированно
        self.structured_logger.error(
            f"Exception occurred: {error_type}",
            extra={
                "error_type": error_type,
                "error_message": error_message,
                "status_code": status_code,
                "path": request.url.path,
                "method": request.method,
                "request_id": error_id,
                "client_ip": request.client.host if request.client else None,
            },
            exc_info=True
        )
        
        # Формируем ответ
        response_data: Dict[str, Any] = {
            "error": error_type,
            "message": error_message,
            "status_code": status_code,
            "request_id": error_id,
            "path": request.url.path,
        }
        
        # Добавляем traceback только в development
        if self.include_traceback:
            response_data["traceback"] = traceback.format_exc()
            response_data["exception_type"] = error_type
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def handle_validation_error(
        self,
        request: Request,
        errors: list,
        status_code: int = 422
    ) -> JSONResponse:
        """
        Обработать ошибки валидации
        
        Args:
            request: HTTP запрос
            errors: Список ошибок валидации
            status_code: HTTP статус код
            
        Returns:
            JSONResponse с информацией об ошибках валидации
        """
        error_id = getattr(request.state, "request_id", None) or "unknown"
        
        # Логируем ошибки валидации
        self.structured_logger.warning(
            "Validation errors",
            extra={
                "errors": errors,
                "path": request.url.path,
                "method": request.method,
                "request_id": error_id,
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "Validation Error",
                "detail": errors,
                "status_code": status_code,
                "request_id": error_id,
                "path": request.url.path,
            }
        )
    
    def handle_http_exception(
        self,
        request: Request,
        exc: HTTPException,
        status_code: Optional[int] = None
    ) -> JSONResponse:
        """
        Обработать HTTP исключение
        
        Args:
            request: HTTP запрос
            exc: HTTP исключение
            status_code: HTTP статус код (если не указан, берется из exc)
            
        Returns:
            JSONResponse с информацией об ошибке
        """
        error_id = getattr(request.state, "request_id", None) or "unknown"
        code = status_code or exc.status_code
        
        # Логируем HTTP ошибки
        log_level = "warning" if code < 500 else "error"
        getattr(self.structured_logger, log_level)(
            f"HTTP {code}: {exc.detail}",
            extra={
                "status_code": code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "request_id": error_id,
            }
        )
        
        return JSONResponse(
            status_code=code,
            content={
                "error": "HTTP Exception",
                "status_code": code,
                "detail": exc.detail,
                "request_id": error_id,
                "path": request.url.path,
            }
        )


# Глобальный экземпляр обработчика ошибок
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Получить глобальный обработчик ошибок
    
    Returns:
        Экземпляр ErrorHandler
    """
    global _error_handler
    
    if _error_handler is None:
        import os
        include_traceback = os.getenv("ENVIRONMENT", "production") == "development"
        _error_handler = ErrorHandler(include_traceback=include_traceback)
    
    return _error_handler


def format_error_for_logging(exc: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Форматировать ошибку для логирования
    
    Args:
        exc: Исключение
        context: Дополнительный контекст
        
    Returns:
        Словарь с информацией об ошибке
    """
    error_info = {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "exception_module": exc.__class__.__module__,
    }
    
    if context:
        error_info.update(context)
    
    return error_info


def log_error_with_context(
    exc: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """
    Логировать ошибку с контекстом
    
    Args:
        exc: Исключение
        context: Дополнительный контекст
        level: Уровень логирования (error, warning, etc.)
    """
    error_info = format_error_for_logging(exc, context)
    structured_logger = get_logger(context=error_info)
    
    getattr(structured_logger, level)(
        f"Exception: {error_info['exception_type']}",
        extra=error_info,
        exc_info=True
    )
