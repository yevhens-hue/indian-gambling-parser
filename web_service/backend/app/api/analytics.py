"""API endpoints для расширенной аналитики"""
from fastapi import APIRouter, Query, Request
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app.services.storage_adapter import StorageAdapter
from app.services.cache import get_cache_service
from app.utils.logger import logger

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    request: Request,
    days: int = Query(7, ge=1, le=365, description="Количество дней для анализа")
):
    """
    Получить ключевые метрики для dashboard (с кэшированием на 5 минут)
    
    Returns:
        - total_providers: Общее количество провайдеров
        - new_today: Новые провайдеры за сегодня
        - new_last_7_days: Новые провайдеры за последние 7 дней
        - active_merchants: Количество активных merchants
        - trends: Тренды по дням
    """
    cache = get_cache_service()
    cache_key = f"analytics:dashboard:days:{days}"
    
    # Пытаемся получить из кэша
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Dashboard metrics получены из кэша для days={days}")
        return cached_result
    
    adapter = StorageAdapter()
    providers = adapter.storage.get_all_providers()
    
    if not providers:
        empty_result = {
            "total_providers": 0,
            "new_today": 0,
            "new_last_7_days": 0,
            "active_merchants": 0,
            "top_merchants": [],
            "top_providers": [],
            "trends": [],
            "account_types_distribution": {},
            "payment_methods_distribution": {}
        }
        # Кэшируем даже пустой результат (меньший TTL)
        cache.set(cache_key, empty_result, ttl=60)
        return empty_result
    
    # Фильтруем по датам
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days_ago = now - timedelta(days=days)
    
    new_today = 0
    new_last_7_days = 0
    trends_by_day = defaultdict(int)
    merchants_count = defaultdict(int)
    providers_count = defaultdict(int)
    account_types = defaultdict(int)
    payment_methods = defaultdict(int)
    
    for provider in providers:
        try:
            # Парсим timestamp
            timestamp_str = provider.get('timestamp_utc', '')
            if timestamp_str:
                if 'T' in timestamp_str:
                    provider_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    provider_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Приводим к локальному времени (без timezone для сравнения)
                if provider_date.tzinfo:
                    provider_date = provider_date.replace(tzinfo=None)
                if now.tzinfo:
                    now_local = now.replace(tzinfo=None)
                else:
                    now_local = now
                    
                days_diff = (now_local - provider_date).days
                
                if provider_date >= today_start:
                    new_today += 1
                
                if days_diff <= 7:
                    new_last_7_days += 1
                
                if days_diff <= days:
                    # Группируем по дням для трендов
                    day_key = provider_date.strftime('%Y-%m-%d')
                    trends_by_day[day_key] += 1
                    
                    # Подсчитываем merchants и providers
                    merchant = provider.get('merchant') or 'unknown'
                    merchants_count[merchant] += 1
                    
                    provider_domain = provider.get('provider_domain') or 'unknown'
                    providers_count[provider_domain] += 1
                    
                    account_type = provider.get('account_type') or 'unknown'
                    account_types[account_type] += 1
                    
                    payment_method = provider.get('payment_method') or 'unknown'
                    payment_methods[payment_method] += 1
        except (ValueError, TypeError) as e:
            # Ошибка парсинга даты - пропускаем запись
            logger.debug(f"Skipping provider due to date parse error: {e}")
            continue
    
    # Формируем тренды (последние N дней)
    trends = []
    for i in range(days):
        date = (now_local - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
        trends.append({
            "date": date,
            "count": trends_by_day.get(date, 0)
        })
    
    # Топ merchants и providers
    top_merchants = sorted(
        merchants_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    top_providers = sorted(
        providers_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    result = {
        "total_providers": len(providers),
        "new_today": new_today,
        "new_last_7_days": new_last_7_days,
        "active_merchants": len(merchants_count),
        "top_merchants": [{"name": name, "count": count} for name, count in top_merchants],
        "top_providers": [{"name": name, "count": count} for name, count in top_providers],
        "trends": trends,
        "account_types_distribution": dict(account_types),
        "payment_methods_distribution": dict(payment_methods)
    }
    
    # Сохраняем в кэш (TTL 5 минут)
    cache.set(cache_key, result, ttl=300)
    logger.debug(f"Dashboard metrics сохранены в кэш для days={days}")
    
    return result


@router.get("/trends")
async def get_trends(
    period: str = Query("7d", regex="^(1d|7d|30d|90d|1y|all)$", description="Период анализа"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Группировка")
):
    """
    Получить тренды по провайдерам за период
    
    Periods:
        - 1d: Последний день
        - 7d: Последняя неделя
        - 30d: Последний месяц
        - 90d: Последние 3 месяца
        - 1y: Последний год
        - all: Все время
    """
    adapter = StorageAdapter()
    providers = adapter.storage.get_all_providers()
    
    # Определяем период
    now = datetime.now()
    if period == "1d":
        start_date = now - timedelta(days=1)
        group_format = "%Y-%m-%d %H:00"
    elif period == "7d":
        start_date = now - timedelta(days=7)
        group_format = "%Y-%m-%d" if group_by == "day" else "%Y-%m-%d"
    elif period == "30d":
        start_date = now - timedelta(days=30)
        group_format = "%Y-%m-%d"
    elif period == "90d":
        start_date = now - timedelta(days=90)
        group_format = "%Y-%m-%d" if group_by == "day" else "%Y-W%W" if group_by == "week" else "%Y-%m"
    elif period == "1y":
        start_date = now - timedelta(days=365)
        group_format = "%Y-%m" if group_by == "month" else "%Y-W%W" if group_by == "week" else "%Y-%m-%d"
    else:  # all
        start_date = datetime(2000, 1, 1)
        group_format = "%Y-%m" if group_by == "month" else "%Y-W%W" if group_by == "week" else "%Y-%m-%d"
    
    trends_by_period = defaultdict(lambda: {
        "total": 0,
        "by_merchant": defaultdict(int),
        "by_account_type": defaultdict(int),
        "by_payment_method": defaultdict(int)
    })
    
    for provider in providers:
        try:
            timestamp_str = provider.get('timestamp_utc', '')
            if not timestamp_str:
                continue
                
            if 'T' in timestamp_str:
                provider_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                provider_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            if provider_date.tzinfo:
                provider_date = provider_date.replace(tzinfo=None)
            
            if provider_date < start_date:
                continue
            
            period_key = provider_date.strftime(group_format)
            trends_by_period[period_key]["total"] += 1
            
            merchant = provider.get('merchant') or 'unknown'
            trends_by_period[period_key]["by_merchant"][merchant] += 1
            
            account_type = provider.get('account_type') or 'unknown'
            trends_by_period[period_key]["by_account_type"][account_type] += 1
            
            payment_method = provider.get('payment_method') or 'unknown'
            trends_by_period[period_key]["by_payment_method"][payment_method] += 1
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"Skipping provider in trends calculation: {e}")
            continue
    
    # Преобразуем в список и сортируем
    trends = []
    for period_key in sorted(trends_by_period.keys()):
        data = trends_by_period[period_key]
        trends.append({
            "period": period_key,
            "total": data["total"],
            "by_merchant": dict(data["by_merchant"]),
            "by_account_type": dict(data["by_account_type"]),
            "by_payment_method": dict(data["by_payment_method"])
        })
    
    return {
        "period": period,
        "group_by": group_by,
        "trends": trends
    }


@router.get("/comparison")
async def compare_merchants(
    merchants: str = Query(..., description="Список merchants через запятую для сравнения")
):
    """
    Сравнение merchants по различным метрикам
    """
    adapter = StorageAdapter()
    providers = adapter.storage.get_all_providers()
    
    merchant_list = [m.strip() for m in merchants.split(',')]
    comparison = {}
    
    for merchant in merchant_list:
        merchant_providers = [p for p in providers if p.get('merchant') == merchant]
        
        if not merchant_providers:
            comparison[merchant] = {
                "total": 0,
                "account_types": {},
                "payment_methods": {},
                "unique_providers": 0,
                "new_last_7_days": 0
            }
            continue
        
        account_types = defaultdict(int)
        payment_methods = defaultdict(int)
        unique_providers = set()
        new_last_7_days = 0
        
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        for provider in merchant_providers:
            account_type = provider.get('account_type') or 'unknown'
            account_types[account_type] += 1
            
            payment_method = provider.get('payment_method') or 'unknown'
            payment_methods[payment_method] += 1
            
            provider_domain = provider.get('provider_domain')
            if provider_domain:
                unique_providers.add(provider_domain)
            
            try:
                timestamp_str = provider.get('timestamp_utc', '')
                if timestamp_str:
                    if 'T' in timestamp_str:
                        provider_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        provider_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if provider_date.tzinfo:
                        provider_date = provider_date.replace(tzinfo=None)
                    
                    if provider_date >= seven_days_ago:
                        new_last_7_days += 1
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse timestamp for comparison: {e}")
        
        comparison[merchant] = {
            "total": len(merchant_providers),
            "account_types": dict(account_types),
            "payment_methods": dict(payment_methods),
            "unique_providers": len(unique_providers),
            "new_last_7_days": new_last_7_days
        }
    
    return {
        "merchants": merchant_list,
        "comparison": comparison
    }


@router.get("/provider-details/{provider_domain}")
async def get_provider_details(
    provider_domain: str,
    days: int = Query(30, ge=1, le=365, description="Период анализа в днях")
):
    """
    Детальная аналитика по конкретному провайдеру
    """
    adapter = StorageAdapter()
    providers = adapter.storage.get_all_providers()
    
    provider_data = [p for p in providers if p.get('provider_domain') == provider_domain]
    
    if not provider_data:
        return {
            "provider_domain": provider_domain,
            "total": 0,
            "merchants": {},
            "account_types": {},
            "timeline": []
        }
    
    merchants = defaultdict(int)
    account_types = defaultdict(int)
    timeline = defaultdict(int)
    
    now = datetime.now()
    days_ago = now - timedelta(days=days)
    
    for provider in provider_data:
        merchant = provider.get('merchant') or 'unknown'
        merchants[merchant] += 1
        
        account_type = provider.get('account_type') or 'unknown'
        account_types[account_type] += 1
        
        try:
            timestamp_str = provider.get('timestamp_utc', '')
            if timestamp_str:
                if 'T' in timestamp_str:
                    provider_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    provider_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                if provider_date.tzinfo:
                    provider_date = provider_date.replace(tzinfo=None)
                
                if provider_date >= days_ago:
                    day_key = provider_date.strftime('%Y-%m-%d')
                    timeline[day_key] += 1
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse timestamp for timeline: {e}")
    
    # Формируем timeline
    timeline_list = []
    for i in range(days):
        date = (now - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
        timeline_list.append({
            "date": date,
            "count": timeline.get(date, 0)
        })
    
    return {
        "provider_domain": provider_domain,
        "total": len(provider_data),
        "merchants": dict(merchants),
        "account_types": dict(account_types),
        "timeline": timeline_list,
        "first_seen": min([p.get('timestamp_utc', '') for p in provider_data], default=''),
        "last_seen": max([p.get('timestamp_utc', '') for p in provider_data], default='')
    }
