"""
Тесты для retry механизма
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "web_service" / "backend"))

from app.utils.retry import retry, RetryError


class TestException(Exception):
    pass


class AnotherException(Exception):
    pass


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Тест успешного выполнения с первой попытки"""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1)
    async def test_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_success_on_second_attempt():
    """Тест успешного выполнения со второй попытки"""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1, exceptions=(TestException,))
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TestException("First attempt failed")
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Тест исчерпания попыток"""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1, exceptions=(TestException,))
    async def test_func():
        nonlocal call_count
        call_count += 1
        raise TestException("Always fails")
    
    with pytest.raises(RetryError):
        await test_func()
    
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_with_different_exception():
    """Тест retry только для определенных исключений"""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1, exceptions=(TestException,))
    async def test_func():
        nonlocal call_count
        call_count += 1
        raise AnotherException("Different exception")
    
    with pytest.raises(AnotherException):
        await test_func()
    
    assert call_count == 1  # Не должно быть retry


def test_retry_sync():
    """Тест синхронной версии retry"""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1, exceptions=(TestException,))
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TestException("First attempt failed")
        return "success"
    
    result = test_func()
    assert result == "success"
    assert call_count == 2
