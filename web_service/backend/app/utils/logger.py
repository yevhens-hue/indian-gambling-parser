"""Настройка структурированного логирования"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированных логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON"""
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем дополнительные поля если они есть
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        # Добавляем exception info если есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Добавляем stack trace для DEBUG уровня
        if record.levelno == logging.DEBUG and record.stack_info:
            log_entry['stack'] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Цветной форматтер для консоли (удобнее для разработки)"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись с цветами"""
        level_color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = f"{level_color}{record.levelname:8s}{reset}"
        module = f"{record.module}:{record.funcName}:{record.lineno}"
        
        message = record.getMessage()
        
        # Добавляем дополнительные поля
        if hasattr(record, 'extra') and record.extra:
            extra_str = ' | '.join(f"{k}={v}" for k, v in record.extra.items())
            message = f"{message} | {extra_str}"
        
        return f"[{timestamp}] {level} | {module} | {message}"


def setup_logger(
    name: str = "providers_api",
    level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Настройка логгера
    
    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Использовать JSON формат (для production) или цветной (для dev)
        log_file: Опциональный файл для записи логов
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Очищаем существующие handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if use_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)
    
    # File handler (если указан)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())  # В файл всегда JSON
        logger.addHandler(file_handler)
    
    # Предотвращаем дублирование логов
    logger.propagate = False
    
    return logger


# Глобальный логгер по умолчанию
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "console")  # "json" или "console"
LOG_FILE = os.getenv("LOG_FILE", None)

logger = setup_logger(
    name="providers_api",
    level=LOG_LEVEL,
    use_json=(LOG_FORMAT == "json"),
    log_file=Path(LOG_FILE) if LOG_FILE else None
)
