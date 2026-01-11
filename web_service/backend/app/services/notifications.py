"""Сервис уведомлений (Email, Telegram, Slack)"""
import os
from typing import Optional, List
from app.utils.logger import logger

# Email уведомления
EMAIL_AVAILABLE = False
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    pass

# Telegram уведомления
TELEGRAM_AVAILABLE = False
try:
    import requests
    TELEGRAM_AVAILABLE = True
except ImportError:
    pass


class NotificationService:
    """Сервис для отправки уведомлений"""
    
    def __init__(self):
        self.email_enabled = False
        self.telegram_enabled = False
        
        # Email настройки
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", self.smtp_user)
        
        if self.smtp_user and self.smtp_password:
            self.email_enabled = EMAIL_AVAILABLE
        
        # Telegram настройки
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if self.telegram_bot_token and self.telegram_chat_id:
            self.telegram_enabled = TELEGRAM_AVAILABLE
    
    def send_email(self, subject: str, body: str, recipients: List[str]) -> bool:
        """
        Отправить email уведомление
        
        Args:
            subject: Тема письма
            body: Тело письма
            recipients: Список получателей
        
        Returns:
            True если успешно, False иначе
        """
        if not self.email_enabled:
            logger.debug("Email notifications disabled")
            return False
        
        if not EMAIL_AVAILABLE:
            logger.warning("Email library not available (smtplib)")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {recipients}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False
    
    def send_telegram(self, message: str) -> bool:
        """
        Отправить Telegram уведомление
        
        Args:
            message: Текст сообщения
        
        Returns:
            True если успешно, False иначе
        """
        if not self.telegram_enabled:
            logger.debug("Telegram notifications disabled")
            return False
        
        if not TELEGRAM_AVAILABLE:
            logger.warning("Telegram library not available (requests)")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}", exc_info=True)
            return False
    
    def notify_new_providers(self, count: int) -> None:
        """Уведомить о новых провайдерах"""
        subject = f"Новые провайдеры: {count}"
        body = f"Импортировано {count} новых провайдеров."
        
        recipients = os.getenv("NOTIFICATION_EMAILS", "").split(",")
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if recipients:
            self.send_email(subject, body, recipients)
        
        telegram_msg = f"🆕 Новые провайдеры: <b>{count}</b>"
        self.send_telegram(telegram_msg)
    
    def notify_import_completed(self, imported: int, errors: int = 0) -> None:
        """Уведомить о завершении импорта"""
        subject = f"Импорт завершен: {imported} записей"
        body = f"Импортировано: {imported}\nОшибок: {errors}"
        
        recipients = os.getenv("NOTIFICATION_EMAILS", "").split(",")
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if recipients:
            self.send_email(subject, body, recipients)
        
        telegram_msg = f"✅ Импорт завершен\nИмпортировано: <b>{imported}</b>\nОшибок: <b>{errors}</b>"
        self.send_telegram(telegram_msg)
    
    def notify_error(self, error_message: str, context: Optional[str] = None) -> None:
        """Уведомить об ошибке"""
        subject = "Ошибка в сервисе провайдеров"
        body = f"Ошибка: {error_message}\n"
        if context:
            body += f"Контекст: {context}"
        
        recipients = os.getenv("ERROR_NOTIFICATION_EMAILS", os.getenv("NOTIFICATION_EMAILS", "")).split(",")
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if recipients:
            self.send_email(subject, body, recipients)
        
        telegram_msg = f"❌ Ошибка: <code>{error_message}</code>"
        if context:
            telegram_msg += f"\nКонтекст: {context}"
        self.send_telegram(telegram_msg)


# Глобальный экземпляр
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Получить глобальный notification service"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
