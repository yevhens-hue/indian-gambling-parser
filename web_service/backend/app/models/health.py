"""Pydantic модели для Health Checks"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class HealthCheckResult(BaseModel):
    """Результат проверки одного компонента"""
    status: str = Field(..., description="Статус: ok, error, warning, disabled, unknown")
    message: str = Field(..., description="Сообщение о статусе")


class HealthCheckResponse(BaseModel):
    """Ответ Health Check endpoint"""
    status: str = Field(..., description="Общий статус: ok или unhealthy")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Результаты проверок компонентов")
    timestamp: str = Field(..., description="Время проверки в ISO формате")
