"""Pytest конфигурация и фикстуры"""
import pytest
import os
import tempfile
import sqlite3
from pathlib import Path
import sys

# Добавляем корневую директорию в путь для импорта storage
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from storage import Storage
except ImportError:
    pytest.skip("storage.py не найден, пропускаем тесты", allow_module_level=True)


@pytest.fixture
def temp_db():
    """Создает временную БД для тестов"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    yield db_path
    
    # Очистка после теста
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def storage(temp_db):
    """Создает Storage экземпляр с временной БД"""
    return Storage(db_path=temp_db, xlsx_path=temp_db.replace('.db', '.xlsx'))


@pytest.fixture
def sample_provider():
    """Пример данных провайдера для тестов"""
    return {
        'merchant': 'test_merchant',
        'merchant_domain': 'test-merchant.com',
        'provider_domain': 'test-provider.com',
        'account_type': 'FTD',
        'provider_name': 'Test Provider',
        'provider_entry_url': 'https://test-provider.com/entry',
        'final_url': 'https://test-provider.com/final',
        'payment_method': 'UPI',
        'is_iframe': False,
        'requires_otp': False,
        'blocked_by_geo': False,
        'captcha_present': False,
    }
