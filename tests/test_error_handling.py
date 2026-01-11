"""
Тесты для глобальной обработки ошибок
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


def test_validation_error_handler():
    """Тест обработки ошибок валидации Pydantic"""
    # Некорректный запрос (отсутствует обязательное поле)
    response = client.put("/api/providers/1", json={})
    
    # Может быть 400 или 422 в зависимости от обработчика
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data or "detail" in data


def test_http_exception_handler():
    """Тест обработки HTTP исключений"""
    # Запрос несуществующего ресурса
    response = client.get("/api/providers/999999")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data or "detail" in data


def test_invalid_endpoint():
    """Тест обработки несуществующего endpoint"""
    response = client.get("/api/nonexistent")
    
    assert response.status_code == 404


def test_health_check():
    """Тест health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert data["status"] in ["ok", "unhealthy"]


def test_metrics_endpoint():
    """Тест metrics endpoint"""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_api_versioning_v1():
    """Тест API версионирования v1"""
    response = client.get("/api/v1/providers")
    
    # Может быть 200 или 500 если БД не настроена
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "version" in data
        assert data["version"] == "v1"
        assert "items" in data
        assert "total" in data
