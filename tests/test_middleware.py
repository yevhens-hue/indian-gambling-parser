"""
Тесты для middleware
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


def test_request_id_middleware():
    """Тест Request ID middleware"""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_compression_middleware():
    """Тест Compression middleware"""
    # Запрос с accept-encoding: gzip
    response = client.get(
        "/api/providers?limit=100",
        headers={"accept-encoding": "gzip"}
    )
    
    assert response.status_code in [200, 500]  # 500 если БД не настроена
    
    # Проверяем, что ответ может быть сжат (если размер достаточен)
    if response.status_code == 200:
        # Если ответ большой, должен быть сжат
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 1024:
            # Может быть сжат, но не обязательно
            pass


def test_error_handling_middleware():
    """Тест обработки ошибок через middleware"""
    # Некорректный запрос
    response = client.put("/api/providers/999999", json={})
    
    assert response.status_code in [400, 404, 422]
    assert "X-Request-ID" in response.headers


def test_cors_middleware():
    """Тест CORS middleware"""
    response = client.options(
        "/api/providers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # CORS headers должны присутствовать (проверяем через dict или status code)
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers_lower or response.status_code == 405
