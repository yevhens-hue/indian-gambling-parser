"""
Тесты для улучшений мониторинга
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.monitoring import get_status, get_metrics_summary, get_performance_info
from app.utils.structured_logging import StructuredLogger, get_logger


def test_structured_logger():
    """Тест структурированного логирования"""
    logger = StructuredLogger(context={"service": "test"})
    
    # Тест базового логирования
    logger.info("Test message", extra={"key": "value"})
    
    # Тест логирования производительности
    logger.log_performance("test_operation", 0.123, {"items": 10})
    
    # Тест логирования события безопасности
    logger.log_security_event("test_event", {"ip": "127.0.0.1"})
    
    # Тест логирования бизнес-события
    logger.log_business_event("provider_added", {"provider_id": "123"})


def test_get_logger():
    """Тест получения логгера"""
    logger = get_logger(context={"request_id": "test-123"})
    assert isinstance(logger, StructuredLogger)
    assert logger.context["request_id"] == "test-123"


def test_monitoring_status_endpoint():
    """Тест endpoint статуса мониторинга"""
    app = FastAPI()
    app.include_router(get_status.__self__.router if hasattr(get_status, '__self__') else None)
    
    # Создаем роутер напрямую
    from app.api.monitoring import router
    app.include_router(router)
    
    client = TestClient(app)
    
    response = client.get("/monitoring/status")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "status" in data
    assert "components" in data


def test_monitoring_metrics_summary():
    """Тест endpoint сводки метрик"""
    from app.api.monitoring import router
    
    app = FastAPI()
    app.include_router(router)
    
    client = TestClient(app)
    
    response = client.get("/monitoring/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data


def test_monitoring_performance():
    """Тест endpoint производительности"""
    from app.api.monitoring import router
    
    app = FastAPI()
    app.include_router(router)
    
    client = TestClient(app)
    
    # Роутер имеет префикс /monitoring, но в main.py добавляется еще /api/monitoring
    # В тесте используем путь без дополнительного префикса
    response = client.get("/monitoring/performance")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    # system или cache могут отсутствовать если psutil не установлен
    assert isinstance(data, dict)
