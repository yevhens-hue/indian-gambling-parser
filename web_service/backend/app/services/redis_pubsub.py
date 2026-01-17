"""
Redis Pub/Sub для распределенных WebSocket уведомлений
"""
import json
import asyncio
from typing import Optional, Callable
import redis.asyncio as aioredis
import os
from app.utils.logger import logger


class RedisPubSub:
    """
    Redis Pub/Sub для распределенных уведомлений
    Позволяет отправлять уведомления между несколькими инстансами приложения
    """
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribed_channels: set = set()
        self.message_handlers: dict = {}
        self._running = False
    
    async def connect(self):
        """Подключение к Redis"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            self.redis_client = aioredis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Проверяем подключение
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            logger.info("Redis Pub/Sub connected successfully")
            
        except Exception as e:
            logger.warning(f"Redis Pub/Sub недоступен: {e}")
            self.redis_client = None
            self.pubsub = None
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        self._running = False
    
    async def publish(self, channel: str, message: dict):
        """
        Публикация сообщения в канал
        
        Args:
            channel: Название канала
            message: Сообщение для отправки
        """
        if not self.redis_client:
            logger.debug("Redis Pub/Sub не подключен, пропускаем публикацию")
            return
        
        try:
            await self.redis_client.publish(channel, json.dumps(message))
            logger.debug(f"Published message to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing to Redis channel {channel}: {e}", exc_info=True)
    
    async def subscribe(self, channel: str, handler: Callable):
        """
        Подписка на канал
        
        Args:
            channel: Название канала
            handler: Функция-обработчик сообщений
        """
        if not self.pubsub:
            await self.connect()
        
        if not self.pubsub:
            logger.warning("Redis Pub/Sub недоступен, подписка невозможна")
            return
        
        try:
            await self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
            self.message_handlers[channel] = handler
            logger.info(f"Subscribed to Redis channel: {channel}")
            
            # Запускаем обработчик сообщений если еще не запущен
            if not self._running:
                asyncio.create_task(self._listen_messages())
                
        except Exception as e:
            logger.error(f"Error subscribing to Redis channel {channel}: {e}", exc_info=True)
    
    async def _listen_messages(self):
        """Прослушивание сообщений из Redis"""
        if not self.pubsub:
            return
        
        self._running = True
        
        try:
            while self._running:
                try:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        channel = message.get("channel")
                        data = message.get("data")
                        
                        if channel and data and channel in self.message_handlers:
                            try:
                                message_data = json.loads(data)
                                handler = self.message_handlers[channel]
                                await handler(channel, message_data)
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in Redis message from channel {channel}")
                            except Exception as e:
                                logger.error(f"Error handling Redis message from channel {channel}: {e}", exc_info=True)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error listening to Redis messages: {e}", exc_info=True)
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Redis Pub/Sub listener stopped: {e}", exc_info=True)
        finally:
            self._running = False
    
    async def notify_provider_update(self, provider_id: int, action: str = "update"):
        """Уведомление об обновлении провайдера"""
        await self.publish("providers:updates", {
            "provider_id": provider_id,
            "action": action,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def notify_import_completed(self, imported: int, errors: int = 0):
        """Уведомление о завершении импорта"""
        await self.publish("import:completed", {
            "imported": imported,
            "errors": errors,
            "timestamp": asyncio.get_event_loop().time()
        })


# Глобальный экземпляр
_redis_pubsub: Optional[RedisPubSub] = None


async def get_redis_pubsub() -> Optional[RedisPubSub]:
    """Получить глобальный экземпляр Redis Pub/Sub"""
    global _redis_pubsub
    
    if _redis_pubsub is None:
        _redis_pubsub = RedisPubSub()
        await _redis_pubsub.connect()
    
    return _redis_pubsub
