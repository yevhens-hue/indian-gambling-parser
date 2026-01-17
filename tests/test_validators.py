"""
Тесты для модуля validators
"""
import pytest
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "web_service" / "backend"))

from app.utils.validators import (
    validate_domain,
    validate_email,
    validate_phone,
    sanitize_string
)


class TestValidateDomain:
    """Тесты для validate_domain"""
    
    def test_valid_domain(self):
        """Валидный домен возвращается без изменений"""
        assert validate_domain("example.com") == "example.com"
        assert validate_domain("sub.example.com") == "sub.example.com"
        assert validate_domain("my-site.co.uk") == "my-site.co.uk"
    
    def test_domain_with_protocol(self):
        """Протокол удаляется"""
        assert validate_domain("https://example.com") == "example.com"
        assert validate_domain("http://example.com") == "example.com"
    
    def test_domain_with_www(self):
        """www. удаляется"""
        assert validate_domain("www.example.com") == "example.com"
        assert validate_domain("https://www.example.com") == "example.com"
    
    def test_domain_with_trailing_slash(self):
        """Trailing slash удаляется"""
        assert validate_domain("example.com/") == "example.com"
        assert validate_domain("https://example.com/") == "example.com"
    
    def test_empty_domain(self):
        """Пустой домен возвращается как есть"""
        assert validate_domain("") == ""
        assert validate_domain(None) is None
    
    def test_invalid_domain(self):
        """Невалидный домен вызывает исключение"""
        with pytest.raises(ValueError, match="Invalid domain format"):
            validate_domain("not-a-domain")
        
        with pytest.raises(ValueError, match="Invalid domain format"):
            validate_domain("example")
        
        with pytest.raises(ValueError, match="Invalid domain format"):
            validate_domain("-invalid.com")


class TestValidateEmail:
    """Тесты для validate_email"""
    
    def test_valid_email(self):
        """Валидный email возвращается в lowercase"""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("USER@EXAMPLE.COM") == "user@example.com"
        assert validate_email("user.name+tag@example.co.uk") == "user.name+tag@example.co.uk"
    
    def test_empty_email(self):
        """Пустой email возвращается как есть"""
        assert validate_email("") == ""
        assert validate_email(None) is None
    
    def test_invalid_email(self):
        """Невалидный email вызывает исключение"""
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("not-an-email")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("missing@domain")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("@nodomain.com")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("spaces in@email.com")


class TestValidatePhone:
    """Тесты для validate_phone"""
    
    def test_valid_phone(self):
        """Валидный телефон очищается от лишних символов"""
        assert validate_phone("+1234567890") == "+1234567890"
        assert validate_phone("(123) 456-7890") == "1234567890"
        assert validate_phone("+1 (234) 567-8901") == "+12345678901"
    
    def test_phone_with_spaces(self):
        """Пробелы удаляются"""
        assert validate_phone("123 456 7890") == "1234567890"
    
    def test_empty_phone(self):
        """Пустой телефон возвращается как есть"""
        assert validate_phone("") == ""
        assert validate_phone(None) is None
    
    def test_invalid_phone(self):
        """Слишком короткий телефон вызывает исключение"""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone("123")
        
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone("12345")


class TestSanitizeString:
    """Тесты для sanitize_string"""
    
    def test_normal_string(self):
        """Обычная строка возвращается без изменений"""
        assert sanitize_string("Hello World") == "Hello World"
        assert sanitize_string("Test 123") == "Test 123"
    
    def test_removes_dangerous_chars(self):
        """Опасные символы удаляются"""
        assert sanitize_string("<script>alert('xss')</script>") == "alert(xss)"
        assert sanitize_string('User "name"') == "User name"
        assert sanitize_string("It's a test") == "Its a test"
    
    def test_max_length(self):
        """Строка обрезается до максимальной длины"""
        long_string = "a" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
        
        result = sanitize_string(long_string)  # default 500
        assert len(result) == 500
    
    def test_strips_whitespace(self):
        """Пробелы по краям удаляются"""
        assert sanitize_string("  hello  ") == "hello"
        assert sanitize_string("\t\ntest\n\t") == "test"
    
    def test_empty_string(self):
        """Пустая строка возвращается как есть"""
        assert sanitize_string("") == ""
        assert sanitize_string(None) is None


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_numeric_tld(self):
        """Домены с цифрами в TLD"""
        # Некоторые TLD содержат цифры
        assert validate_domain("example.c0m") == "example.c0m"
        assert validate_domain("test.123") == "test.123"
    
    def test_unicode_in_email(self):
        """Юникод в email"""
        # Современные email могут содержать юникод в локальной части
        assert validate_email("user@example.com") == "user@example.com"
    
    def test_special_chars_in_phone(self):
        """Специальные символы в телефоне"""
        assert validate_phone("+7 (999) 123-45-67") == "+79991234567"
        assert validate_phone("8-800-555-35-35") == "88005553535"
    
    def test_sanitize_html(self):
        """Санитизация HTML"""
        html = "<div onclick='evil()'>Content</div>"
        result = sanitize_string(html)
        assert "<" not in result
        assert ">" not in result
        assert "onclick" not in result
        assert result == "Content"
    
    def test_sanitize_javascript_url(self):
        """Санитизация javascript: URL"""
        js_url = "javascript:alert('xss')"
        result = sanitize_string(js_url)
        assert "javascript:" not in result.lower()
    
    def test_sanitize_event_handlers(self):
        """Санитизация event handlers"""
        text = 'text onerror="alert(1)" more'
        result = sanitize_string(text)
        assert "onerror" not in result
