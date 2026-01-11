"""Pydantic models для валидации данных провайдеров"""
from pydantic import BaseModel, HttpUrl, Field, validator, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class ProviderBase(BaseModel):
    """Базовая модель провайдера с валидацией"""
    merchant: str = Field(..., min_length=1, max_length=100, description="Название мерчанта")
    merchant_domain: str = Field(..., min_length=1, max_length=255, description="Домен мерчанта")
    provider_domain: str = Field(..., min_length=1, max_length=255, description="Домен провайдера")
    account_type: Optional[str] = Field(None, max_length=100, description="Тип аккаунта")
    provider_name: Optional[str] = Field(None, max_length=255, description="Название провайдера")
    provider_entry_url: Optional[str] = Field(None, max_length=2048, description="URL входа")
    final_url: Optional[str] = Field(None, max_length=2048, description="Финальный URL")
    cashier_url: Optional[str] = Field(None, max_length=2048, description="URL кассы")
    screenshot_path: Optional[str] = Field(None, max_length=512, description="Путь к скриншоту")
    detected_in: Optional[str] = Field(None, max_length=255, description="Где обнаружен")
    payment_method: Optional[str] = Field(None, max_length=100, description="Метод оплаты")
    is_iframe: bool = Field(False, description="Использует iframe")
    requires_otp: bool = Field(False, description="Требует OTP")
    blocked_by_geo: bool = Field(False, description="Заблокирован по гео")
    captcha_present: bool = Field(False, description="Есть капча")
    
    @field_validator('merchant_domain', 'provider_domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Валидация домена"""
        if not v:
            raise ValueError('Domain cannot be empty')
        # Базовая проверка формата домена
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, v):
            raise ValueError(f'Invalid domain format: {v}')
        return v.lower()
    
    @field_validator('provider_entry_url', 'final_url', 'cashier_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Валидация URL"""
        if v is None or v == '':
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'URL must start with http:// or https://: {v}')
        if len(v) > 2048:
            raise ValueError(f'URL too long (max 2048): {len(v)}')
        return v


class ProviderCreate(ProviderBase):
    """Модель для создания провайдера"""
    pass


class ProviderUpdate(BaseModel):
    """Модель для обновления провайдера (все поля опциональны)"""
    merchant: Optional[str] = Field(None, min_length=1, max_length=100)
    merchant_domain: Optional[str] = Field(None, min_length=1, max_length=255)
    provider_domain: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[str] = Field(None, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=255)
    provider_entry_url: Optional[str] = Field(None, max_length=2048)
    final_url: Optional[str] = Field(None, max_length=2048)
    cashier_url: Optional[str] = Field(None, max_length=2048)
    screenshot_path: Optional[str] = Field(None, max_length=512)
    detected_in: Optional[str] = Field(None, max_length=255)
    payment_method: Optional[str] = Field(None, max_length=100)
    is_iframe: Optional[bool] = None
    requires_otp: Optional[bool] = None
    blocked_by_geo: Optional[bool] = None
    captcha_present: Optional[bool] = None
    
    @field_validator('merchant_domain', 'provider_domain')
    @classmethod
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        """Валидация домена"""
        if v is None or v == '':
            return v
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, v):
            raise ValueError(f'Invalid domain format: {v}')
        return v.lower()
    
    @field_validator('provider_entry_url', 'final_url', 'cashier_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Валидация URL"""
        if v is None or v == '':
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'URL must start with http:// or https://: {v}')
        return v


class Provider(ProviderBase):
    """Модель провайдера с ID и timestamp"""
    id: Optional[int] = None
    timestamp_utc: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProvidersResponse(BaseModel):
    """Ответ API со списком провайдеров"""
    items: list[Provider]
    total: int
    skip: int
    limit: int
    has_more: bool


class StatisticsResponse(BaseModel):
    """Ответ API со статистикой"""
    total: int = Field(..., ge=0, description="Общее количество провайдеров")
    merchants: dict[str, int] = Field(default_factory=dict, description="Количество по мерчантам")
    account_types: dict[str, int] = Field(default_factory=dict, description="Количество по типам аккаунтов")
    payment_methods: dict[str, int] = Field(default_factory=dict, description="Количество по методам оплаты")
    providers: dict[str, int] = Field(default_factory=dict, description="Количество по провайдерам")


class BatchDeleteRequest(BaseModel):
    """Запрос на массовое удаление провайдеров"""
    ids: List[int] = Field(..., min_length=1, max_length=1000, description="Список ID для удаления")
    
    @field_validator('ids')
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        """Валидация ID"""
        if not v:
            raise ValueError('IDs list cannot be empty')
        if len(v) > 1000:
            raise ValueError(f'Too many IDs (max 1000): {len(v)}')
        if any(id <= 0 for id in v):
            raise ValueError('All IDs must be positive integers')
        return sorted(set(v))  # Убираем дубликаты и сортируем


class BatchUpdateRequest(BaseModel):
    """Запрос на массовое обновление провайдеров"""
    ids: List[int] = Field(..., min_length=1, max_length=100, description="Список ID для обновления")
    updates: Dict[str, Any] = Field(..., description="Поля для обновления")
    
    @field_validator('ids')
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        """Валидация ID"""
        if not v:
            raise ValueError('IDs list cannot be empty')
        if len(v) > 100:
            raise ValueError(f'Too many IDs for batch update (max 100): {len(v)}')
        return sorted(set(v))


class BatchDeleteResponse(BaseModel):
    """Ответ на массовое удаление"""
    deleted_count: int = Field(..., ge=0, description="Количество удаленных записей")
    not_found_ids: List[int] = Field(default_factory=list, description="ID которые не были найдены")


class BatchUpdateResponse(BaseModel):
    """Ответ на массовое обновление"""
    updated_count: int = Field(..., ge=0, description="Количество обновленных записей")
    not_found_ids: List[int] = Field(default_factory=list, description="ID которые не были найдены")
    failed_ids: List[int] = Field(default_factory=list, description="ID при обновлении которых произошла ошибка")
