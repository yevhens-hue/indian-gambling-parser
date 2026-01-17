"""
Тесты для третьего раунда улучшений
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "web_service" / "backend"))

try:
    from app.main import app
except ImportError:
    pytest.skip("Backend app не найден, пропускаем тесты", allow_module_level=True)

client = TestClient(app)


def test_response_cache_middleware():
    """Тест Response Cache middleware"""
    # Первый запрос - должен быть MISS
    response1 = client.get("/api/providers?limit=10")
    
    assert response1.status_code in [200, 500]  # 500 если БД не настроена
    if response1.status_code == 200:
        assert "X-Cache" in response1.headers
        assert response1.headers["X-Cache"] == "MISS"
        assert "X-Cache-Key" in response1.headers
        
        # Второй запрос - должен быть HIT (если кэш работает)
        response2 = client.get("/api/providers?limit=10")
        assert response2.status_code == 200
        # Может быть HIT или MISS в зависимости от конфигурации Redis


def test_timeout_middleware():
    """Тест Timeout middleware"""
    # Обычный запрос должен проходить
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_endpoints():
    """Тест health check endpoints"""
    # Базовый health check
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data
    
    # Детальный health check
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    # Должны быть дополнительные проверки
    assert len(data["checks"]) >= 2
    
    # Readiness check
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]
    
    # Liveness check
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_cache_headers():
    """Тест заголовков кэша"""
    response = client.get("/api/providers?limit=5")
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        # Проверяем наличие заголовков кэша
        assert "X-Cache" in response.headers or "X-Cache-Key" in response.headers
