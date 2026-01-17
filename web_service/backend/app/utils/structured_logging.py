"""
Утилиты для структурированного логирования
"""
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from app.utils.logger import logger


class StructuredLogger:
    """
    Класс для структурированного логирования с контекстом
    """
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Args:
            context: Базовый контекст для всех логов
        """
        self.context = context or {}
    
    def _merge_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Объединить базовый контекст с дополнительными данными
        
        Args:
            extra: Дополнительные данные для логирования
            
        Returns:
            Объединенный контекст
        """
        merged = self.context.copy()
        if extra:
            merged.update(extra)
        
        # Добавляем timestamp
        merged["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        return merged
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Логировать информационное сообщение"""
        logger.info(message, extra=self._merge_context(extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Логировать предупреждение"""
        logger.warning(message, extra=self._merge_context(extra))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Логировать ошибку"""
        logger.error(message, extra=self._merge_context(extra), exc_info=exc_info)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Логировать отладочное сообщение"""
        logger.debug(message, extra=self._merge_context(extra))
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Логировать метрику производительности
        
        Args:
            operation: Название операции
            duration: Время выполнения в секундах
            metadata: Дополнительные метаданные
        """
        extra = {
            "operation": operation,
            "duration_seconds": round(duration, 3),
            "duration_ms": round(duration * 1000, 2),
        }
        if metadata:
            extra.update(metadata)
        
        self.info(f"Performance: {operation}", extra=extra)
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ):
        """
        Логировать событие безопасности
        
        Args:
            event_type: Тип события (login, access_denied, etc.)
            details: Детали события
        """
        extra = {
            "event_type": event_type,
            "security_event": True,
        }
        extra.update(details)
        
        self.warning(f"Security event: {event_type}", extra=extra)
    
    def log_business_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ):
        """
        Логировать бизнес-событие
        
        Args:
            event_type: Тип события (provider_added, export_completed, etc.)
            details: Детали события
        """
        extra = {
            "event_type": event_type,
            "business_event": True,
        }
        extra.update(details)
        
        self.info(f"Business event: {event_type}", extra=extra)


def get_logger(context: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """
    Получить экземпляр структурированного логгера
    
    Args:
        context: Базовый контекст
        
    Returns:
        Экземпляр StructuredLogger
    """
    return StructuredLogger(context=context)
