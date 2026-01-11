"""Настройка Sentry для отслеживания ошибок"""
import os
from typing import Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


def init_sentry(dsn: Optional[str] = None, environment: Optional[str] = None) -> bool:
    """
    Инициализация Sentry для отслеживания ошибок
    
    Args:
        dsn: Sentry DSN (если None, берется из SENTRY_DSN env var)
        environment: Окружение (development, staging, production)
    
    Returns:
        True если Sentry успешно инициализирован, False иначе
    """
    if not SENTRY_AVAILABLE:
        return False
    
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        return False
    
    environment = environment or os.getenv("ENVIRONMENT", "development")
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Отслеживание производительности (10% запросов)
            traces_sample_rate=0.1,
            # Отслеживание профилирования (только для медленных запросов)
            profiles_sample_rate=0.1,
            # Отправка локальных переменных (только для development)
            send_default_pii=environment == "development",
            # Игнорировать некоторые исключения
            ignore_errors=[
                KeyboardInterrupt,
            ],
            # Дополнительная информация
            release=os.getenv("RELEASE_VERSION", "unknown"),
            server_name=os.getenv("SERVER_NAME", "unknown"),
        )
        return True
    except Exception as e:
        # Не падаем если Sentry не работает
        try:
            from app.utils.logger import logger
            logger.warning(f"Sentry initialization failed: {e}")
        except ImportError:
            print(f"⚠️  Sentry initialization failed: {e}")
        return False
