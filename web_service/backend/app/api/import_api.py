"""API endpoints для импорта данных из Google Sheets

Файл переименован в import_api.py, так как 'import' - зарезервированное слово в Python
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.google_sheets_importer import GoogleSheetsImporter
from app.services.cache import get_cache_service
from app.utils.logger import logger

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/google-sheets")
async def import_from_google_sheets(
    sheet_name: Optional[str] = Query(None, description="Название листа (например, 'Scraper (PY)')"),
    gid: Optional[str] = Query(None, description="ID листа (gid из URL, например '396039446')"),
):
    """
    Импорт данных провайдеров из Google Sheets в БД
    
    Примеры использования:
    - Импорт из листа по gid: `/api/import/google-sheets?gid=396039446`
    - Импорт из листа по имени: `/api/import/google-sheets?sheet_name=Scraper (PY)`
    """
    try:
        importer = GoogleSheetsImporter()
        result = importer.import_from_sheet(sheet_name=sheet_name, gid=gid)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Инвалидируем кэш после успешного импорта
        if result.get("imported", 0) > 0:
            cache = get_cache_service()
            cache.invalidate_providers()
            cache.invalidate_statistics()
            logger.info(
                f"Cache invalidated after import: {result.get('imported', 0)} providers imported"
            )
            
            # Отправляем WebSocket уведомление
            try:
                from app.services.websocket_notifier import notify_import_completed
                notify_import_completed(
                    imported=result.get("imported", 0),
                    errors=result.get("errors", 0)
                )
            except Exception as e:
                logger.debug(f"WebSocket notification failed: {e}")
            
            # Отправляем email/Telegram уведомление (если настроено)
            try:
                from app.services.notifications import get_notification_service
                notification_service = get_notification_service()
                notification_service.notify_import_completed(
                    imported=result.get("imported", 0),
                    errors=result.get("errors", 0)
                )
            except Exception as e:
                logger.debug(f"Notification service failed: {e}")
        
        return result
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Файл credentials не найден: {str(e)}")
    except Exception as e:
        logger.error(
            "Error importing from Google Sheets",
            extra={"error": str(e), "sheet_name": sheet_name, "gid": gid},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка при импорте: {str(e)}")


@router.get("/google-sheets/preview")
async def preview_google_sheets(
    sheet_name: Optional[str] = Query(None, description="Название листа"),
    gid: Optional[str] = Query(None, description="ID листа (gid из URL)"),
    limit: int = Query(10, ge=1, le=100, description="Количество строк для предпросмотра"),
):
    """
    Предпросмотр данных из Google Sheets перед импортом
    
    Возвращает первые N строк для проверки корректности парсинга
    """
    try:
        importer = GoogleSheetsImporter()
        providers = importer.parse_google_sheets_data(sheet_name=sheet_name, gid=gid)
        
        # Возвращаем только первые N записей
        preview = providers[:limit]
        
        return {
            "status": "success",
            "total_found": len(providers),
            "preview_count": len(preview),
            "preview": preview,
            "columns": [
                "merchant", "merchant_domain", "account_type", "provider_domain",
                "provider_name", "provider_entry_url", "final_url", "payment_method"
            ] if preview else []
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при предпросмотре: {str(e)}")
