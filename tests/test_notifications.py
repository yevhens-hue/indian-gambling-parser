"""
Тесты для модуля notifications
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent.parent / "web_service" / "backend"))

from app.services.notifications import NotificationService, get_notification_service


class TestNotificationServiceInit:
    """Тесты инициализации NotificationService"""
    
    def test_default_init(self):
        """Инициализация без переменных окружения"""
        with patch.dict('os.environ', {}, clear=True):
            service = NotificationService()
            assert service.email_enabled is False
            assert service.telegram_enabled is False
    
    def test_email_enabled_with_credentials(self):
        """Email включен если есть credentials"""
        env = {
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "password123"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            assert service.email_enabled is True
            assert service.smtp_user == "user@example.com"
            assert service.smtp_password == "password123"
    
    def test_telegram_enabled_with_credentials(self):
        """Telegram включен если есть bot token и chat id"""
        env = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC",
            "TELEGRAM_CHAT_ID": "12345"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            assert service.telegram_enabled is True
            assert service.telegram_bot_token == "123456:ABC"
            assert service.telegram_chat_id == "12345"
    
    def test_custom_smtp_settings(self):
        """Кастомные SMTP настройки"""
        env = {
            "SMTP_HOST": "smtp.custom.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "user",
            "SMTP_PASSWORD": "pass"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            assert service.smtp_host == "smtp.custom.com"
            assert service.smtp_port == 465


class TestSendEmail:
    """Тесты отправки email"""
    
    def test_email_disabled_returns_false(self):
        """Возвращает False если email отключен"""
        with patch.dict('os.environ', {}, clear=True):
            service = NotificationService()
            result = service.send_email("Test", "Body", ["test@example.com"])
            assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Успешная отправка email"""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        env = {
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "password",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            result = service.send_email(
                subject="Test Subject",
                body="Test Body",
                recipients=["recipient@example.com"]
            )
            
            assert result is True
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Ошибка при отправке email"""
        mock_smtp.side_effect = Exception("SMTP error")
        
        env = {
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "password"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            result = service.send_email("Test", "Body", ["test@example.com"])
            assert result is False


class TestSendTelegram:
    """Тесты отправки в Telegram"""
    
    def test_telegram_disabled_returns_false(self):
        """Возвращает False если Telegram отключен"""
        with patch.dict('os.environ', {}, clear=True):
            service = NotificationService()
            result = service.send_telegram("Test message")
            assert result is False
    
    @patch('requests.post')
    def test_send_telegram_success(self, mock_post):
        """Успешная отправка в Telegram"""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        env = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC",
            "TELEGRAM_CHAT_ID": "12345"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            result = service.send_telegram("Test message")
            
            assert result is True
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "123456:ABC" in call_args[0][0]
            assert call_args[1]["json"]["chat_id"] == "12345"
            assert call_args[1]["json"]["text"] == "Test message"
    
    @patch('requests.post')
    def test_send_telegram_failure(self, mock_post):
        """Ошибка при отправке в Telegram"""
        mock_post.side_effect = Exception("Network error")
        
        env = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC",
            "TELEGRAM_CHAT_ID": "12345"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            result = service.send_telegram("Test message")
            assert result is False


class TestNotificationMethods:
    """Тесты методов уведомлений"""
    
    @patch.object(NotificationService, 'send_email')
    @patch.object(NotificationService, 'send_telegram')
    def test_notify_new_providers(self, mock_telegram, mock_email):
        """Уведомление о новых провайдерах"""
        env = {
            "NOTIFICATION_EMAILS": "admin@example.com, ops@example.com",
            "TELEGRAM_BOT_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "chat"
        }
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            service.notify_new_providers(10)
            
            # Проверяем вызов email
            mock_email.assert_called_once()
            call_args = mock_email.call_args
            assert "10" in call_args[0][0]  # subject содержит count
            assert ["admin@example.com", "ops@example.com"] == call_args[0][2]
            
            # Проверяем вызов telegram
            mock_telegram.assert_called_once()
            assert "10" in mock_telegram.call_args[0][0]
    
    @patch.object(NotificationService, 'send_email')
    @patch.object(NotificationService, 'send_telegram')
    def test_notify_import_completed(self, mock_telegram, mock_email):
        """Уведомление о завершении импорта"""
        env = {"NOTIFICATION_EMAILS": "admin@example.com"}
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            service.notify_import_completed(imported=100, errors=5)
            
            mock_email.assert_called_once()
            mock_telegram.assert_called_once()
            
            # Проверяем содержимое
            email_body = mock_email.call_args[0][1]
            assert "100" in email_body
            assert "5" in email_body
    
    @patch.object(NotificationService, 'send_email')
    @patch.object(NotificationService, 'send_telegram')
    def test_notify_error(self, mock_telegram, mock_email):
        """Уведомление об ошибке"""
        env = {"ERROR_NOTIFICATION_EMAILS": "errors@example.com"}
        with patch.dict('os.environ', env, clear=True):
            service = NotificationService()
            service.notify_error("Database connection failed", context="import_job")
            
            mock_email.assert_called_once()
            email_args = mock_email.call_args[0]
            assert "Ошибка" in email_args[0]  # subject
            assert "Database connection failed" in email_args[1]  # body
            assert "import_job" in email_args[1]  # context in body
    
    @patch.object(NotificationService, 'send_email')
    @patch.object(NotificationService, 'send_telegram')
    def test_notify_error_without_context(self, mock_telegram, mock_email):
        """Уведомление об ошибке без контекста"""
        service = NotificationService()
        service.notify_error("Simple error")
        
        mock_telegram.assert_called_once()
        telegram_msg = mock_telegram.call_args[0][0]
        assert "Simple error" in telegram_msg


class TestGetNotificationService:
    """Тесты получения глобального сервиса"""
    
    def test_get_notification_service_singleton(self):
        """Возвращает один и тот же экземпляр"""
        # Сбрасываем глобальную переменную
        import app.services.notifications as notifications_module
        notifications_module._notification_service = None
        
        service1 = get_notification_service()
        service2 = get_notification_service()
        
        assert service1 is service2
    
    def test_get_notification_service_type(self):
        """Возвращает NotificationService"""
        import app.services.notifications as notifications_module
        notifications_module._notification_service = None
        
        service = get_notification_service()
        assert isinstance(service, NotificationService)
