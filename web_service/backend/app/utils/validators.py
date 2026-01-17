"""
Дополнительные валидаторы для данных
"""
from pydantic import field_validator
from typing import Any
import re


def validate_domain(domain: str) -> str:
    """
    Валидация домена
    """
    if not domain:
        return domain
    
    # Удаляем протокол если есть
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
    
    # Удаляем trailing slash
    domain = domain.rstrip("/")
    
    # Базовая проверка формата домена (включая punycode для IDN)
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9]{2,}$'
    if not re.match(domain_pattern, domain):
        raise ValueError(f"Invalid domain format: {domain}")
    
    return domain


def validate_email(email: str) -> str:
    """
    Валидация email адреса
    """
    if not email:
        return email
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    
    return email.lower()


def validate_phone(phone: str) -> str:
    """
    Валидация телефонного номера
    """
    if not phone:
        return phone
    
    # Удаляем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Базовая проверка
    if len(cleaned) < 10:
        raise ValueError(f"Invalid phone number: {phone}")
    
    return cleaned


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Санитизация строки от XSS и инъекций
    """
    if not value:
        return value
    
    # Удаляем HTML теги полностью
    sanitized = re.sub(r'<[^>]*>', '', value)
    
    # Удаляем опасные атрибуты (onclick, onerror, etc.)
    sanitized = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'\s*on\w+\s*=\s*\S+', '', sanitized, flags=re.IGNORECASE)
    
    # Удаляем javascript: и data: URLs
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'data:', '', sanitized, flags=re.IGNORECASE)
    
    # Удаляем опасные символы
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    # Обрезаем до максимальной длины
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()
