"""API endpoints для Health Checks"""
from fastapi import APIRouter
from app.models.health import HealthCheckResponse
from app.main import app
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint с детальными проверками
    
    Returns:
        - status: ok/unhealthy
        - checks: результаты проверок компонентов
        - timestamp: время проверки
    """
    # Используем существующий endpoint из main.py
    # Этот роутер добавлен для документации, реальный endpoint в main.py
    pass
