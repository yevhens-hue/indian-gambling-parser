"""Pydantic модели для Health Checks"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class HealthCheck(BaseModel):
    """Результат проверки одного компонента"""
    status: str = Field(..., description="Статус: ok, error, warning, disabled, unknown")
    message: str = Field(..., description="Сообщение о статусе")
    enabled: Optional[bool] = Field(None, description="Включен ли компонент")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали")


class HealthResponse(BaseModel):
    """Ответ Health Check endpoint"""
    status: str = Field(..., description="Общий статус: ok, warning, error")
    checks: Dict[str, HealthCheck] = Field(..., description="Результаты проверок компонентов")
    timestamp: str = Field(..., description="Время проверки в ISO формате")


# Для обратной совместимости
HealthCheckResponse = HealthResponse
HealthCheckResult = HealthCheck
