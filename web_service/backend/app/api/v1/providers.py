"""
API v1: Providers endpoints
Версионированная версия providers API
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body, Request
from typing import Optional, List, Dict, Any
from app.services.storage_adapter import StorageAdapter
from app.utils.logger import logger
from app.services.cache import get_cache_service
from app.services.audit_log import get_audit_log_service
from pydantic import BaseModel, Field

class ProviderUpdate(BaseModel):
    """Модель для обновления провайдера"""
    merchant: Optional[str] = Field(None, description="Мерчант")
    provider_domain: Optional[str] = Field(None, description="Домен провайдера")
    provider_name: Optional[str] = Field(None, description="Имя провайдера")
    account_type: Optional[str] = Field(None, description="Тип аккаунта")
    payment_method: Optional[str] = Field(None, description="Метод оплаты")

class BatchDeleteRequest(BaseModel):
    """Модель для массового удаления"""
    provider_ids: List[int] = Field(..., description="Список ID провайдеров для удаления")

class BatchUpdateRequest(BaseModel):
    """Модель для массового обновления"""
    provider_ids: List[int] = Field(..., description="Список ID провайдеров")
    updates: Dict[str, Any] = Field(..., description="Обновления для применения")

router = APIRouter(
    prefix="/providers",
    tags=["providers-v1"],
    responses={404: {"description": "Not found"}}
)

storage_adapter = StorageAdapter()


@router.get("")
async def get_providers_v1(
    request: Request,
    merchant: Optional[str] = Query(None, description="Фильтр по мерчанту"),
    provider_domain: Optional[str] = Query(None, description="Фильтр по домену провайдера"),
    account_type: Optional[str] = Query(None, description="Фильтр по типу аккаунта"),
    payment_method: Optional[str] = Query(None, description="Фильтр по методу оплаты"),
    search: Optional[str] = Query(None, description="Поиск по имени провайдера"),
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(50, ge=1, le=1000, description="Максимальное количество записей"),
    sort_by: str = Query("timestamp_utc", description="Поле для сортировки"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Порядок сортировки")
):
    """
    Получить список провайдеров (API v1)
    
    - **merchant**: Фильтр по мерчанту
    - **provider_domain**: Фильтр по домену провайдера
    - **account_type**: Фильтр по типу аккаунта
    - **payment_method**: Фильтр по методу оплаты
    - **search**: Поиск по имени провайдера
    - **skip**: Количество записей для пропуска (пагинация)
    - **limit**: Максимальное количество записей
    - **sort_by**: Поле для сортировки
    - **sort_order**: Порядок сортировки (asc/desc)
    
    Returns:
        - total: Общее количество записей
        - items: Список провайдеров
        - skip: Количество пропущенных записей
        - limit: Лимит записей
    """
    try:
        cache = get_cache_service()
        
        # Кэш ключ
        cache_key = f"providers_v1:{merchant}:{provider_domain}:{account_type}:{payment_method}:{search}:{skip}:{limit}:{sort_by}:{sort_order}"
        
        # Попытка получить из кэша
        if cache.enabled:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for providers_v1: {cache_key[:50]}")
                return cached
        
        try:
            result = storage_adapter.get_all_providers(
                merchant=merchant,
                provider_domain=provider_domain,
                account_type=account_type,
                payment_method=payment_method,
                search=search,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
        except Exception as e:
            logger.error(f"Error in storage_adapter.get_all_providers: {e}", exc_info=True)
            raise
        
        response = {
            "total": result.get("total", 0),
            "items": result.get("items", []),  # storage_adapter возвращает "items"
            "skip": skip,
            "limit": limit,
            "version": "v1"
        }
        
        # Сохраняем в кэш (TTL 60 секунд)
        if cache.enabled:
            cache.set(cache_key, response, ttl=60)
        
        return response
    except Exception as e:
        logger.error(f"Error getting providers v1: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении провайдеров: {str(e)}")


@router.get("/{provider_id}")
async def get_provider_by_id_v1(
    provider_id: int = Path(..., description="ID провайдера", gt=0)
):
    """
    Получить провайдера по ID (API v1)
    
    - **provider_id**: ID провайдера
    
    Returns:
        - provider: Данные провайдера
    """
    try:
        provider = storage_adapter.get_provider_by_id(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Провайдер с ID {provider_id} не найден")
        
        return {
            "provider": provider,
            "version": "v1"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider v1 by ID: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении провайдера: {str(e)}")


@router.put("/{provider_id}")
async def update_provider_v1(
    request: Request,
    provider_id: int = Path(..., description="ID провайдера", gt=0),
    updates: ProviderUpdate = Body(..., description="Обновления провайдера")
):
    """
    Обновить провайдера (API v1)
    
    - **provider_id**: ID провайдера
    - **updates**: Данные для обновления
    
    Returns:
        - success: Успешность операции
        - provider: Обновленные данные провайдера
    """
    try:
        # Получаем старые значения для audit log
        old_provider = storage_adapter.get_provider_by_id(provider_id)
        if not old_provider:
            raise HTTPException(status_code=404, detail=f"Провайдер с ID {provider_id} не найден")
        
        updates_dict = updates.dict(exclude_unset=True)
        success = storage_adapter.update_provider(provider_id, updates_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось обновить провайдера")
        
        new_provider = storage_adapter.get_provider_by_id(provider_id)
        
        # Логируем в audit log
        try:
            audit_service = get_audit_log_service()
            audit_service.log_action(
                table_name="providers",
                action="UPDATE",
                record_id=provider_id,
                old_values=old_provider,
                new_values=new_provider,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as e:
            logger.debug(f"Audit log failed: {e}")
        
        # Инвалидируем кэш
        cache = get_cache_service()
        if cache.enabled:
            cache.delete_pattern("providers_v1:*")
        
        return {
            "success": True,
            "provider": new_provider,
            "version": "v1"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider v1: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении провайдера: {str(e)}")
