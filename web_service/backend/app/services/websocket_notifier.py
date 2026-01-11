"""Сервис для отправки WebSocket уведомлений"""
from typing import Optional, Dict, Any
from app.utils.logger import logger

# Глобальный экземпляр ConnectionManager (будет установлен при инициализации)
_connection_manager: Optional[Any] = None


def set_connection_manager(manager: Any):
    """Установить ConnectionManager для отправки уведомлений"""
    global _connection_manager
    _connection_manager = manager
    logger.debug("WebSocket ConnectionManager установлен для уведомлений")


def notify_providers_updated(count: Optional[int] = None, action: str = "updated"):
    """
    Уведомить всех подключенных клиентов об обновлении провайдеров
    
    Args:
        count: Количество обновленных провайдеров (опционально)
        action: Тип действия (updated, deleted, created)
    """
    if not _connection_manager:
        return
    
    try:
        message = {
            "type": "providers_updated",
            "action": action,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }
        if count is not None:
            message["count"] = count
        
        # Используем asyncio для асинхронной отправки
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже работает, создаем задачу
            asyncio.create_task(_connection_manager.broadcast(message))
        else:
            # Иначе запускаем синхронно
            asyncio.run(_connection_manager.broadcast(message))
        
        logger.debug(f"WebSocket уведомление отправлено: {action}")
    except Exception as e:
        logger.warning(f"Ошибка отправки WebSocket уведомления: {e}", exc_info=True)


def notify_statistics_updated():
    """Уведомить всех подключенных клиентов об обновлении статистики"""
    if not _connection_manager:
        return
    
    try:
        message = {
            "type": "statistics_updated",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }
        
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_connection_manager.broadcast(message))
        else:
            asyncio.run(_connection_manager.broadcast(message))
        
        logger.debug("WebSocket уведомление: statistics_updated")
    except Exception as e:
        logger.warning(f"Ошибка отправки WebSocket уведомления о статистике: {e}", exc_info=True)


def notify_import_completed(imported: int, errors: int = 0):
    """
    Уведомить об завершении импорта данных
    
    Args:
        imported: Количество импортированных записей
        errors: Количество ошибок
    """
    if not _connection_manager:
        return
    
    try:
        message = {
            "type": "import_completed",
            "imported": imported,
            "errors": errors,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }
        
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_connection_manager.broadcast(message))
        else:
            asyncio.run(_connection_manager.broadcast(message))
        
        logger.debug(f"WebSocket уведомление: import_completed ({imported} imported, {errors} errors)")
    except Exception as e:
        logger.warning(f"Ошибка отправки WebSocket уведомления об импорте: {e}", exc_info=True)
