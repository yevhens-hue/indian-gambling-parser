"""Сервис метрик Prometheus"""
from typing import Optional
import time
from fastapi import Request
from fastapi.responses import Response

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest,
        CONTENT_TYPE_LATEST, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Заглушки для случаев когда prometheus_client не установлен
    Counter = Histogram = Gauge = None
    def generate_latest():
        return b"# Prometheus metrics disabled (prometheus-client not installed)\n"
    CONTENT_TYPE_LATEST = "text/plain"
    REGISTRY = None


class MetricsService:
    """Сервис для сбора метрик Prometheus"""
    
    def __init__(self):
        """Инициализация метрик"""
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            try:
                from app.utils.logger import logger
                logger.warning("Prometheus client не установлен. Метрики отключены.")
            except ImportError:
                print("⚠️  Prometheus client не установлен. Метрики отключены.")
            return
        
        # HTTP метрики
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Бизнес метрики
        self.providers_total = Gauge(
            'providers_total',
            'Total number of providers in database'
        )
        
        self.providers_by_merchant = Gauge(
            'providers_by_merchant',
            'Number of providers by merchant',
            ['merchant']
        )
        
        # Кэш метрики
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_key_prefix']
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_key_prefix']
        )
        
        # БД метрики
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
        )
        
        # WebSocket метрики
        self.websocket_connections_active = Gauge(
            'websocket_connections_active',
            'Active WebSocket connections'
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Записать метрику HTTP запроса"""
        if not self.enabled:
            return
        
        # Нормализуем endpoint (убираем параметры)
        normalized_endpoint = endpoint.split('?')[0] if '?' in endpoint else endpoint
        
        self.http_requests_total.labels(
            method=method,
            endpoint=normalized_endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=normalized_endpoint
        ).observe(duration)
    
    def record_cache_hit(self, cache_key_prefix: str):
        """Записать попадание в кэш"""
        if not self.enabled:
            return
        self.cache_hits_total.labels(cache_key_prefix=cache_key_prefix).inc()
    
    def record_cache_miss(self, cache_key_prefix: str):
        """Записать промах кэша"""
        if not self.enabled:
            return
        self.cache_misses_total.labels(cache_key_prefix=cache_key_prefix).inc()
    
    def update_providers_count(self, total: int, by_merchant: Optional[dict] = None):
        """Обновить счетчик провайдеров"""
        if not self.enabled:
            return
        
        self.providers_total.set(total)
        
        if by_merchant:
            for merchant, count in by_merchant.items():
                self.providers_by_merchant.labels(merchant=merchant).set(count)
    
    def record_db_query(self, query_type: str, duration: float):
        """Записать метрику запроса к БД"""
        if not self.enabled:
            return
        self.db_query_duration_seconds.labels(query_type=query_type).observe(duration)
    
    def update_websocket_connections(self, count: int):
        """Обновить количество активных WebSocket соединений"""
        if not self.enabled:
            return
        self.websocket_connections_active.set(count)
    
    def generate_metrics(self) -> bytes:
        """Сгенерировать метрики в формате Prometheus"""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return b"# Prometheus metrics disabled (prometheus-client not installed)\n"
        try:
            return generate_latest(REGISTRY)
        except Exception as e:
            try:
                from app.utils.logger import logger
                logger.error(f"Ошибка генерации метрик: {e}", exc_info=True)
            except:
                pass
            return b"# Error generating metrics\n"


# Глобальный экземпляр metrics service
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Получить глобальный metrics service (singleton)"""
    global _metrics_service
    
    if _metrics_service is None:
        _metrics_service = MetricsService()
    
    return _metrics_service
