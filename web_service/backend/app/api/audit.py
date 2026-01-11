"""API endpoints для audit log"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.services.audit_log import get_audit_log_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/log")
async def get_audit_log(
    table_name: Optional[str] = Query(None, description="Фильтр по таблице"),
    record_id: Optional[int] = Query(None, description="Фильтр по ID записи"),
    action: Optional[str] = Query(None, description="Фильтр по действию (INSERT, UPDATE, DELETE)"),
    limit: int = Query(100, ge=1, le=1000, description="Максимум записей")
) -> List[Dict[str, Any]]:
    """
    Получить записи из audit log (история изменений)
    
    Returns список действий с данными о том, кто, когда и что изменил
    """
    try:
        audit_service = get_audit_log_service()
        logs = audit_service.get_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=action,
            limit=limit
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении audit log: {str(e)}")


@router.get("/log/{record_id}")
async def get_audit_log_for_record(
    record_id: int,
    table_name: str = Query("providers", description="Название таблицы"),
    limit: int = Query(50, ge=1, le=100, description="Максимум записей")
) -> List[Dict[str, Any]]:
    """
    Получить историю изменений для конкретной записи
    """
    try:
        audit_service = get_audit_log_service()
        logs = audit_service.get_audit_log(
            table_name=table_name,
            record_id=record_id,
            limit=limit
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении audit log: {str(e)}")
