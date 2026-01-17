"""Адаптер для работы с существующим Storage классом"""
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from app.config import BASE_DIR, DB_PATH, XLSX_PATH, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_PATH
from app.services.cache import get_cache_service
from app.services.metrics import get_metrics_service
from app.utils.logger import logger

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(BASE_DIR))

try:
    from storage import Storage
except ImportError:
    raise ImportError(
        f"Не удалось импортировать storage.py. "
        f"Убедитесь, что файл существует в {BASE_DIR}"
    )


class StorageAdapter:
    """Адаптер для интеграции существующего Storage с FastAPI"""
    
    def __init__(self, use_pool: bool = True):
        """
        Инициализация адаптера с существующим Storage
        
        Args:
            use_pool: Использовать connection pool (по умолчанию True для backend)
        """
        self.storage = Storage(
            db_path=DB_PATH,
            xlsx_path=XLSX_PATH,
            google_sheet_id=GOOGLE_SHEET_ID if GOOGLE_SHEET_ID else None,
            google_credentials_path=GOOGLE_CREDENTIALS_PATH if os.path.exists(GOOGLE_CREDENTIALS_PATH) else None,
            use_pool=use_pool,
            pool_size=5  # Размер pool для backend
        )
    
    def get_all_providers(
        self,
        merchant: Optional[str] = None,
        provider_domain: Optional[str] = None,
        account_type: Optional[str] = None,
        payment_method: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "timestamp_utc",
        sort_order: str = "desc",
        search: Optional[str] = None
    ) -> Dict:
        """
        Получить список провайдеров с фильтрацией, сортировкой и пагинацией
        
        Использует оптимизированный SQL запрос с фильтрацией и пагинацией
        на уровне базы данных.
        
        Args:
            merchant: Фильтр по мерчанту
            provider_domain: Фильтр по домену провайдера
            account_type: Фильтр по типу аккаунта
            payment_method: Фильтр по методу оплаты
            skip: Пропустить N записей (для пагинации)
            limit: Максимум записей
            sort_by: Поле для сортировки
            sort_order: Порядок сортировки (asc/desc)
            search: Текстовый поиск по всем полям
        
        Returns:
            Словарь с items, total, skip, limit, has_more
        """
        # Замеряем время выполнения запроса
        start_time = time.time()
        
        # Используем оптимизированный метод с SQL пагинацией
        result = self.storage.get_providers_paginated(
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
        
        # Записываем метрику времени выполнения БД запроса
        db_duration = time.time() - start_time
        metrics = get_metrics_service()
        metrics.record_db_query("get_providers_paginated", db_duration)
        
        # Убеждаемся, что ID присутствует (для React ключей)
        for i, provider in enumerate(result["items"]):
            if 'id' not in provider or provider['id'] is None:
                provider['id'] = skip + i + 1
        
        return result
    
    def get_provider_by_id(self, provider_id: int) -> Optional[Dict]:
        """Получить провайдера по ID"""
        providers = self.storage.get_all_providers()
        for provider in providers:
            if provider.get('id') == provider_id:
                return provider
        return None
    
    def update_provider(self, provider_id: int, updates: Dict) -> bool:
        """
        Обновить данные провайдера
        
        Args:
            provider_id: ID провайдера
            updates: Словарь с обновлениями
        
        Returns:
            True если успешно, False иначе
        """
        # Получаем текущие данные
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return False
        
        # Обновляем поля через существующий метод save_provider
        # (он делает INSERT OR REPLACE по уникальному ключу)
        try:
            self.storage.save_provider(
                merchant=updates.get('merchant', provider.get('merchant')),
                merchant_domain=updates.get('merchant_domain', provider.get('merchant_domain')),
                provider_domain=updates.get('provider_domain', provider.get('provider_domain')),
                account_type=updates.get('account_type', provider.get('account_type')),
                provider_name=updates.get('provider_name', provider.get('provider_name')),
                provider_entry_url=updates.get('provider_entry_url', provider.get('provider_entry_url')),
                final_url=updates.get('final_url', provider.get('final_url')),
                cashier_url=updates.get('cashier_url', provider.get('cashier_url')),
                screenshot_path=updates.get('screenshot_path', provider.get('screenshot_path')),
                detected_in=updates.get('detected_in', provider.get('detected_in')),
                payment_method=updates.get('payment_method', provider.get('payment_method')),
                is_iframe=updates.get('is_iframe', bool(provider.get('is_iframe'))),
                requires_otp=updates.get('requires_otp', bool(provider.get('requires_otp'))),
                blocked_by_geo=updates.get('blocked_by_geo', bool(provider.get('blocked_by_geo'))),
                captcha_present=updates.get('captcha_present', bool(provider.get('captcha_present'))),
            )
            return True
        except Exception as e:
            print(f"Ошибка при обновлении провайдера: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Получить статистику по провайдерам"""
        providers = self.storage.get_all_providers()
        
        if not providers:
            return {
                "total": 0,
                "merchants": {},
                "account_types": {},
                "payment_methods": {},
                "providers": {}
            }
        
        # Фильтруем None значения перед подсчетом
        df_dict = {
            'merchant': [p.get('merchant') for p in providers if p.get('merchant')],
            'account_type': [p.get('account_type') for p in providers if p.get('account_type')],
            'payment_method': [p.get('payment_method') for p in providers if p.get('payment_method')],
            'provider_domain': [p.get('provider_domain') for p in providers if p.get('provider_domain')],
        }
        
        # Подсчет статистики
        from collections import Counter
        
        # Создаем словари, фильтруя None ключи
        merchants = dict(Counter(df_dict['merchant']))
        account_types = dict(Counter(df_dict['account_type']))
        payment_methods = dict(Counter(df_dict['payment_method']))
        providers_count = dict(Counter(df_dict['provider_domain']))
        
        # Убеждаемся, что все значения - строки (не None)
        merchants = {str(k): int(v) for k, v in merchants.items() if k is not None}
        account_types = {str(k): int(v) for k, v in account_types.items() if k is not None}
        payment_methods = {str(k): int(v) for k, v in payment_methods.items() if k is not None}
        providers_count = {str(k): int(v) for k, v in providers_count.items() if k is not None}
        
        stats = {
            "total": len(providers),
            "merchants": merchants,
            "account_types": account_types,
            "payment_methods": payment_methods,
            "providers": providers_count
        }
        
        # Обновляем метрики Prometheus
        metrics = get_metrics_service()
        metrics.update_providers_count(total=len(providers), by_merchant=merchants)
        
        # Сохраняем в кэш (TTL 5 минут)
        cache.set(cache_key, stats, ttl=300)
        logger.debug("Statistics сохранены в кэш")
        
        return stats
    
    def export_to_xlsx(self, output_path: Optional[str] = None) -> str:
        """Экспорт в XLSX"""
        self.storage.export_to_xlsx(output_path)
        return output_path or XLSX_PATH
    
    def delete_provider(self, provider_id: int) -> bool:
        """Удалить провайдера по ID"""
        return self.storage.delete_provider(provider_id)
    
    def batch_delete_providers(self, provider_ids: List[int]) -> Dict[str, Any]:
        """Массовое удаление провайдеров"""
        return self.storage.batch_delete_providers(provider_ids)
    
    def batch_update_providers(self, provider_ids: List[int], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Массовое обновление провайдеров
        
        Args:
            provider_ids: Список ID для обновления
            updates: Словарь с полями для обновления
        
        Returns:
            dict с ключами: updated_count, not_found_ids, failed_ids
        """
        updated_count = 0
        not_found_ids = []
        failed_ids = []
        
        for provider_id in provider_ids:
            try:
                success = self.update_provider(provider_id, updates)
                if success:
                    updated_count += 1
                else:
                    not_found_ids.append(provider_id)
            except Exception as e:
                logger.error(f"Ошибка при batch обновлении провайдера {provider_id}: {e}", exc_info=True)
                failed_ids.append(provider_id)
        
        return {
            "updated_count": updated_count,
            "not_found_ids": not_found_ids,
            "failed_ids": failed_ids
        }