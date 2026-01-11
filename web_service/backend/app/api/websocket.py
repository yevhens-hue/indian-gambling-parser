"""WebSocket endpoints для real-time обновлений"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from datetime import datetime
from app.services.storage_adapter import StorageAdapter
from app.services.metrics import get_metrics_service
from app.services.websocket_notifier import set_connection_manager
from app.utils.logger import logger as app_logger

router = APIRouter(prefix="/ws", tags=["websocket"])

# Глобальный экземпляр ConnectionManager
manager = None

def get_connection_manager():
    """Получить глобальный ConnectionManager"""
    global manager
    if manager is None:
        manager = ConnectionManager()
        # Устанавливаем для websocket_notifier
        set_connection_manager(manager)
    return manager

# Хранилище активных подключений
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.storage_adapter = StorageAdapter()
        self.last_data_hash = None
        self.monitoring_task = None

    async def connect(self, websocket: WebSocket):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket подключен. Всего подключений: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Отключение клиента"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Обновляем метрики
        metrics = get_metrics_service()
        metrics.update_websocket_connections(len(self.active_connections))
        
        app_logger.info(f"WebSocket отключен. Осталось подключений: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Отправка личного сообщения"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            app_logger.error(f"Ошибка отправки WebSocket сообщения: {e}", exc_info=True)
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                app_logger.warning(f"Ошибка WebSocket broadcast: {e}")
                disconnected.append(connection)
        
        # Удаляем отключенные соединения
        for conn in disconnected:
            self.disconnect(conn)

    async def check_for_updates(self):
        """Проверка изменений в БД и отправка обновлений"""
        while True:
            try:
                await asyncio.sleep(5)  # Проверка каждые 5 секунд
                
                if not self.active_connections:
                    continue
                
                # Получаем текущие данные
                providers = self.storage_adapter.storage.get_all_providers()
                current_hash = hash(str([(p.get('id'), p.get('timestamp_utc')) for p in providers[:10]]))
                
                # Если данные изменились
                if current_hash != self.last_data_hash:
                    self.last_data_hash = current_hash
                    
                    # Получаем статистику
                    stats = self.storage_adapter.get_statistics()
                    
                    # Отправляем обновление всем клиентам
                    await self.broadcast({
                        "type": "data_updated",
                        "timestamp": datetime.utcnow().isoformat(),
                        "statistics": stats,
                    "total_providers": len(providers)
                })
                    
            except Exception as e:
                app_logger.error(f"Ошибка при проверке WebSocket обновлений: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def start_monitoring(self):
        """Запуск мониторинга изменений"""
        if self.monitoring_task is None or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self.check_for_updates())


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для real-time обновлений данных"""
    manager = get_connection_manager()
    await manager.connect(websocket)
    
    # Запускаем мониторинг, если еще не запущен
    await manager.start_monitoring()
    
    # Отправляем начальные данные
    try:
        stats = manager.storage_adapter.get_statistics()
        providers = manager.storage_adapter.storage.get_all_providers()
        
        await manager.send_personal_message(
            json.dumps({
                "type": "initial_data",
                "timestamp": datetime.utcnow().isoformat(),
                "statistics": stats,
                "total_providers": len(providers)
            }),
            websocket
        )
    except Exception as e:
        app_logger.error(f"Ошибка отправки начальных WebSocket данных: {e}", exc_info=True)
    
    try:
        # Поддерживаем соединение и слушаем сообщения от клиента
        while True:
            data = await websocket.receive_text()
            # Эхо-ответ (клиент может отправлять ping)
            if data == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        app_logger.error(f"Ошибка WebSocket соединения: {e}", exc_info=True)
        manager.disconnect(websocket)


@router.post("/trigger-update")
async def trigger_update():
    """Триггер для принудительной отправки обновления всем клиентам"""
    try:
        manager = get_connection_manager()
        stats = manager.storage_adapter.get_statistics()
        providers = manager.storage_adapter.storage.get_all_providers()
        
        await manager.broadcast({
            "type": "manual_update",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats,
            "total_providers": len(providers)
        })
        
        return {"status": "ok", "message": "Update sent to all clients", "clients": len(manager.active_connections)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
