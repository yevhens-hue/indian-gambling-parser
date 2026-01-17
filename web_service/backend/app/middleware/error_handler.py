"""
Глобальная обработка ошибок и исключений (улучшенная версия)
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.error_handler import get_error_handler


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обработчик ошибок валидации Pydantic (улучшенный)
    """
    error_handler = get_error_handler()
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    return error_handler.handle_validation_error(request, errors)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Обработчик HTTP исключений (улучшенный)
    """
    error_handler = get_error_handler()
    return error_handler.handle_http_exception(request, exc)


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Обработчик всех необработанных исключений (улучшенный)
    """
    error_handler = get_error_handler()
    
    # Определяем статус код в зависимости от типа исключения
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = None
    
    # Специальная обработка для некоторых типов исключений
    if isinstance(exc, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        detail = str(exc)
    elif isinstance(exc, PermissionError):
        status_code = status.HTTP_403_FORBIDDEN
        detail = "Permission denied"
    elif isinstance(exc, FileNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        detail = "Resource not found"
    
    return error_handler.handle_exception(request, exc, status_code, detail)
