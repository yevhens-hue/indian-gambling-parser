"""
Глобальная обработка ошибок и исключений
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger import logger
import traceback
from typing import Any, Dict


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обработчик ошибок валидации Pydantic
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "errors": errors,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": errors,
            "path": str(request.url.path)
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Обработчик HTTP исключений
    """
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Обработчик всех необработанных исключений
    """
    error_traceback = traceback.format_exc()
    
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": str(request.url.path),
            "method": request.method,
            "traceback": error_traceback
        },
        exc_info=True
    )
    
    # В production не показываем полный traceback
    import os
    is_development = os.getenv("ENVIRONMENT", "production") == "development"
    
    response_content: Dict[str, Any] = {
        "error": "Internal Server Error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "An unexpected error occurred",
        "path": str(request.url.path)
    }
    
    if is_development:
        response_content["traceback"] = error_traceback
        response_content["exception_type"] = type(exc).__name__
        response_content["exception_message"] = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content
    )
