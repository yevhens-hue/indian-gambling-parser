"""API endpoints для работы с провайдерами"""
from fastapi import APIRouter, HTTPException, Query, Path, Body, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.storage_adapter import StorageAdapter
from app.services.cache import get_cache_service
from app.models.provider import (
    Provider, ProvidersResponse, StatisticsResponse,
    BatchDeleteRequest, BatchDeleteResponse,
    BatchUpdateRequest, BatchUpdateResponse,
    ProviderUpdate
)
from app.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.utils.logger import logger

router = APIRouter(prefix="/providers", tags=["providers"])
storage_adapter = StorageAdapter()

# Rate limiter будет использоваться из app.state.limiter


@router.get("", response_model=ProvidersResponse)
async def get_providers(
    request: Request,
    merchant: Optional[str] = Query(None, description="Фильтр по мерчанту"),
    provider_domain: Optional[str] = Query(None, description="Фильтр по домену провайдера"),
    account_type: Optional[str] = Query(None, description="Фильтр по типу аккаунта"),
    payment_method: Optional[str] = Query(None, description="Фильтр по методу оплаты"),
    search: Optional[str] = Query(None, description="Текстовый поиск по всем полям"),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Максимум записей"),
    sort_by: str = Query("timestamp_utc", description="Поле для сортировки"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Порядок сортировки"),
):
    """
    Получить список провайдеров с фильтрацией, сортировкой и пагинацией
    
    Rate limit: 100 запросов в минуту (применяется глобально)
    """
    try:
        logger.debug(
            "Fetching providers",
            extra={
                "merchant": merchant,
                "provider_domain": provider_domain,
                "account_type": account_type,
                "skip": skip,
                "limit": limit,
            }
        )
        
        result = storage_adapter.get_all_providers(
            merchant=merchant,
            provider_domain=provider_domain,
            account_type=account_type,
            payment_method=payment_method,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search
        )
        
        # Преобразуем в модели Pydantic
        providers = [Provider(**item) for item in result["items"]]
        
        logger.info(
            "Providers fetched successfully",
            extra={
                "total": result["total"],
                "returned": len(providers),
                "has_more": result["has_more"]
            }
        )
        
        return ProvidersResponse(
            items=providers,
            total=result["total"],
            skip=result["skip"],
            limit=result["limit"],
            has_more=result["has_more"]
        )
    except Exception as e:
        logger.error(
            "Error fetching providers",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")


@router.get("/{provider_id}", response_model=Provider)
async def get_provider(
    request: Request,
    provider_id: int = Path(..., description="ID провайдера")
):
    """
    Получить провайдера по ID
    """
    provider = storage_adapter.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Провайдер с ID {provider_id} не найден")
    return Provider(**provider)


@router.put("/{provider_id}", response_model=Provider)
async def update_provider(
    request: Request,
    provider_id: int = Path(..., ge=1, description="ID провайдера"),
    updates: ProviderUpdate = Body(..., description="Обновляемые поля")
):
    """
    Обновить данные провайдера
    
    Все поля опциональны. Отправляйте только те поля, которые нужно обновить.
    """
    # Преобразуем Pydantic модель в dict, исключая None значения
    updates_dict = updates.model_dump(exclude_unset=True, exclude_none=True)
    
    if not updates_dict:
        raise HTTPException(status_code=400, detail="Не указаны поля для обновления")
    
    # Получаем старые значения для audit log
    old_provider = storage_adapter.get_provider_by_id(provider_id)
    
    success = storage_adapter.update_provider(provider_id, updates_dict)
    if not success:
        raise HTTPException(status_code=404, detail=f"Провайдер с ID {provider_id} не найден")
    
    # Логируем в audit log
    try:
        from app.services.audit_log import get_audit_log_service
        from app.services.storage_adapter import StorageAdapter
        audit_service = get_audit_log_service()
        
        # Получаем новые значения
        new_provider = storage_adapter.get_provider_by_id(provider_id)
        
        audit_service.log_action(
            table_name="providers",
            action="UPDATE",
            record_id=provider_id,
            old_values=old_provider if old_provider else None,
            new_values=new_provider if new_provider else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception as e:
        logger.debug(f"Audit log failed: {e}")
    
    # Инвалидируем кэш при изменении данных
    cache = get_cache_service()
    cache.invalidate_providers()
    cache.invalidate_statistics()
    logger.info(f"Cache invalidated after provider update: {provider_id}")
    
    # Отправляем WebSocket уведомление
    try:
        from app.services.websocket_notifier import notify_providers_updated
        notify_providers_updated(count=1, action="updated")
    except Exception as e:
        logger.debug(f"WebSocket notification failed: {e}")
    
    # Возвращаем обновленные данные
    provider = storage_adapter.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Провайдер с ID {provider_id} не найден после обновления")
    return Provider(**provider)


@router.get("/stats/statistics", response_model=StatisticsResponse)
async def get_statistics(request: Request):
    """
    Получить статистику по провайдерам (с кэшированием на 5 минут)
    """
    try:
        stats = storage_adapter.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(
            "Error fetching statistics",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(request: Request):
    """
    Очистить кэш (admin функция)
    
    Параметры query:
    - pattern: Паттерн для очистки (например, "providers:*", "statistics:*")
             Если не указан, очищаются все провайдеры и статистика
    """
    cache = get_cache_service()
    
    if not cache.enabled:
        return {
            "status": "skipped",
            "message": "Cache is not enabled (Redis unavailable)"
        }
    
    pattern = request.query_params.get("pattern")
    
    if pattern:
        cleared = cache.clear_pattern(pattern)
        logger.info(f"Cache cleared for pattern: {pattern}, keys: {cleared}")
        return {
            "status": "success",
            "pattern": pattern,
            "cleared_keys": cleared
        }
    else:
        # Очищаем все кэши провайдеров и статистики
        providers_cleared = cache.invalidate_providers()
        stats_cleared = cache.invalidate_statistics()
        total = providers_cleared + stats_cleared
        
        logger.info(f"Cache cleared: providers={providers_cleared}, statistics={stats_cleared}, total={total}")
        
        return {
            "status": "success",
            "cleared_keys": total,
            "providers_keys": providers_cleared,
            "statistics_keys": stats_cleared
        }


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_providers(
    request: Request,
    batch_request: BatchDeleteRequest = Body(..., description="Запрос на массовое удаление")
):
    """
    Массовое удаление провайдеров
    
    Удаляет до 1000 провайдеров за раз. ID валидируются автоматически.
    """
    try:
        result = storage_adapter.batch_delete_providers(batch_request.ids)
        
        # Инвалидируем кэш при изменении данных
        if result["deleted_count"] > 0:
            cache = get_cache_service()
            cache.invalidate_providers()
            cache.invalidate_statistics()
            logger.info(f"Batch delete: {result['deleted_count']} providers deleted, cache invalidated")
            
            # Отправляем WebSocket уведомление
            try:
                from app.services.websocket_notifier import notify_providers_updated
                notify_providers_updated(count=result["deleted_count"], action="deleted")
            except Exception as e:
                logger.debug(f"WebSocket notification failed: {e}")
        
        return BatchDeleteResponse(
            deleted_count=result["deleted_count"],
            not_found_ids=result["not_found_ids"]
        )
    except Exception as e:
        logger.error(
            "Error in batch delete",
            extra={"ids": batch_request.ids, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка при массовом удалении: {str(e)}")


@router.put("/batch-update", response_model=BatchUpdateResponse)
async def batch_update_providers(
    request: Request,
    batch_request: BatchUpdateRequest = Body(..., description="Запрос на массовое обновление")
):
    """
    Массовое обновление провайдеров
    
    Обновляет до 100 провайдеров за раз. Все провайдеры получат одинаковые обновления.
    Поля валидируются через Pydantic.
    """
    try:
        # Валидируем обновления через ProviderUpdate
        provider_update = ProviderUpdate(**batch_request.updates)
        updates_dict = provider_update.model_dump(exclude_unset=True, exclude_none=True)
        
        if not updates_dict:
            raise HTTPException(status_code=400, detail="Не указаны поля для обновления")
        
        result = storage_adapter.batch_update_providers(batch_request.ids, updates_dict)
        
        # Инвалидируем кэш при изменении данных
        if result["updated_count"] > 0:
            cache = get_cache_service()
            cache.invalidate_providers()
            cache.invalidate_statistics()
            logger.info(f"Batch update: {result['updated_count']} providers updated, cache invalidated")
            
            # Отправляем WebSocket уведомление
            try:
                from app.services.websocket_notifier import notify_providers_updated
                notify_providers_updated(count=result["updated_count"], action="updated")
            except Exception as e:
                logger.debug(f"WebSocket notification failed: {e}")
        
        return BatchUpdateResponse(
            updated_count=result["updated_count"],
            not_found_ids=result["not_found_ids"],
            failed_ids=result["failed_ids"]
        )
    except Exception as e:
        logger.error(
            "Error in batch update",
            extra={"ids": batch_request.ids, "error": str(e)},
            exc_info=True
        )
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Ошибка при массовом обновлении: {str(e)}")
