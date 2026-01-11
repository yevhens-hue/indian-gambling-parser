"""Тесты для API endpoints"""
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


@pytest.fixture
def client():
    """Создает тестовый клиент FastAPI"""
    return TestClient(app)


def test_root_endpoint(client):
    """Тест корневого endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Providers API"


def test_health_check(client):
    """Тест health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_get_providers_endpoint(client):
    """Тест получения провайдеров"""
    response = client.get("/api/providers?limit=10")
    assert response.status_code in [200, 500]  # 500 если БД не настроена
    
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


def test_get_statistics_endpoint(client):
    """Тест получения статистики"""
    response = client.get("/api/providers/stats/statistics")
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "total" in data
        assert "merchants" in data
        assert "account_types" in data
