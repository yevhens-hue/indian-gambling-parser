"""Тесты для Storage класса"""
import os
import sqlite3
import pytest
from storage import Storage


def test_storage_initialization(temp_db):
    """Тест инициализации Storage"""
    storage = Storage(db_path=temp_db)
    assert storage is not None
    assert os.path.exists(temp_db)


def test_database_has_indexes(storage):
    """Тест наличия индексов в БД"""
    # Инициализируем БД чтобы создать индексы
    storage.init_database()
    
    # Подключаемся к БД и проверяем индексы
    conn = sqlite3.connect(storage.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND tbl_name='providers' AND name NOT LIKE 'sqlite_%'
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Проверяем основные индексы
    expected_indexes = [
        'idx_merchant',
        'idx_provider_domain',
        'idx_timestamp',
    ]
    
    for idx_name in expected_indexes:
        assert idx_name in indexes, f"Индекс {idx_name} не найден. Найдены индексы: {indexes}"


def test_save_provider(storage, sample_provider):
    """Тест сохранения провайдера"""
    result = storage.save_provider(**sample_provider)
    assert result is True
    
    # Проверяем, что провайдер сохранен
    providers = storage.get_all_providers()
    assert len(providers) == 1
    assert providers[0]['merchant'] == sample_provider['merchant']
    assert providers[0]['provider_domain'] == sample_provider['provider_domain']


def test_save_provider_duplicate(storage, sample_provider):
    """Тест сохранения дубликата (должен обновить)"""
    # Сохраняем первый раз
    storage.save_provider(**sample_provider)
    
    # Сохраняем второй раз с другим именем (должно обновиться)
    updated_provider = sample_provider.copy()
    updated_provider['provider_name'] = 'Updated Provider Name'
    result = storage.save_provider(**updated_provider)
    
    assert result is True
    
    # Проверяем, что запись обновилась, а не создалась новая
    providers = storage.get_all_providers()
    assert len(providers) == 1
    assert providers[0]['provider_name'] == 'Updated Provider Name'


def test_get_all_providers(storage, sample_provider):
    """Тест получения всех провайдеров"""
    # Сохраняем несколько провайдеров
    for i in range(3):
        provider = sample_provider.copy()
        provider['merchant'] = f"merchant_{i}"
        provider['provider_domain'] = f"provider-{i}.com"
        storage.save_provider(**provider)
    
    providers = storage.get_all_providers()
    assert len(providers) == 3


def test_get_all_providers_with_filter(storage, sample_provider):
    """Тест фильтрации провайдеров"""
    # Сохраняем провайдеров с разными мерчантами
    provider1 = sample_provider.copy()
    provider1['merchant'] = 'merchant_1'
    storage.save_provider(**provider1)
    
    provider2 = sample_provider.copy()
    provider2['merchant'] = 'merchant_2'
    provider2['provider_domain'] = 'provider2.com'
    storage.save_provider(**provider2)
    
    # Фильтруем по мерчанту
    providers = storage.get_all_providers(merchant='merchant_1')
    assert len(providers) == 1
    assert providers[0]['merchant'] == 'merchant_1'


def test_normalize_domain(storage):
    """Тест нормализации доменов"""
    test_cases = [
        ('https://subdomain.example.com/path', 'example.com'),
        ('http://test.co.in/page', 'test.co.in'),
        ('https://www.test.com', 'test.com'),
        ('invalid-url', ''),
        ('', ''),
    ]
    
    for url, expected in test_cases:
        result = storage.normalize_domain(url)
        assert result == expected, f"Для {url} ожидалось {expected}, получено {result}"


def test_provider_exists(storage, sample_provider):
    """Тест проверки существования провайдера"""
    # Провайдер не должен существовать
    exists = storage.provider_exists(
        merchant_domain=sample_provider['merchant_domain'],
        provider_domain=sample_provider['provider_domain'],
        account_type=sample_provider['account_type']
    )
    assert exists is False
    
    # Сохраняем провайдера
    storage.save_provider(**sample_provider)
    
    # Теперь должен существовать
    exists = storage.provider_exists(
        merchant_domain=sample_provider['merchant_domain'],
        provider_domain=sample_provider['provider_domain'],
        account_type=sample_provider['account_type']
    )
    assert exists is True


def test_empty_database(storage):
    """Тест работы с пустой БД"""
    providers = storage.get_all_providers()
    assert isinstance(providers, list)
    assert len(providers) == 0
