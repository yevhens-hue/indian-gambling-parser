"""Сервис для импорта данных из Google Sheets"""
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
import tldextract
from datetime import datetime, timezone

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

from app.services.storage_adapter import StorageAdapter
from app.config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_PATH, BASE_DIR


class GoogleSheetsImporter:
    """Импорт данных из Google Sheets в БД"""
    
    def __init__(self):
        self.storage_adapter = StorageAdapter()
        self.google_sheet_id = GOOGLE_SHEET_ID
        self.google_credentials_path = GOOGLE_CREDENTIALS_PATH if os.path.exists(GOOGLE_CREDENTIALS_PATH) else None
    
    def normalize_domain(self, url: str) -> str:
        """Нормализация домена (eTLD+1)"""
        if not url or not url.startswith(("http://", "https://")):
            return ""
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}".lower()
            return extracted.domain.lower() if extracted.domain else ""
        except Exception:
            return ""
    
    def extract_provider_from_url(self, url: str) -> str:
        """Извлечь домен провайдера из URL"""
        if not url:
            return "unknown"
        
        # Обрабатываем сложные URL типа "https://1win.com/https://cai-pay.net/..."
        if "http://" in url or "https://" in url:
            # Берем последний URL из строки
            urls = url.split("https://")
            if len(urls) > 1:
                url = "https://" + urls[-1]
            else:
                urls = url.split("http://")
                if len(urls) > 1:
                    url = "http://" + urls[-1]
        
        return self.normalize_domain(url) or "unknown"
    
    def parse_google_sheets_data(self, sheet_name: str = None, gid: Optional[str] = None) -> List[Dict]:
        """
        Парсинг данных из Google Sheets
        
        Args:
            sheet_name: Название листа (например, "Scraper (PY)")
            gid: ID листа (gid из URL, например "396039446")
        
        Returns:
            Список словарей с данными провайдеров
        """
        if not GOOGLE_SHEETS_AVAILABLE:
            raise Exception("Google Sheets API не доступен. Установите: pip install gspread google-auth")
        
        if not self.google_credentials_path or not os.path.exists(self.google_credentials_path):
            raise FileNotFoundError(f"Файл credentials не найден: {self.google_credentials_path}")
        
        if not self.google_sheet_id:
            raise ValueError("Google Sheet ID не указан")
        
        # Аутентификация
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(
            self.google_credentials_path,
            scopes=scope
        )
        client = gspread.authorize(creds)
        
        # Открываем таблицу
        sheet = client.open_by_key(self.google_sheet_id)
        
        # Выбираем нужный лист
        if gid:
            # Если указан gid, пробуем найти лист по gid
            try:
                worksheet = sheet.get_worksheet_by_id(int(gid))
            except:
                # Если не получилось, используем первый лист
                worksheet = sheet.sheet1
        elif sheet_name:
            try:
                worksheet = sheet.worksheet(sheet_name)
            except:
                worksheet = sheet.sheet1
        else:
            worksheet = sheet.sheet1
        
        # Читаем данные
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            return []
        
        # Определяем заголовки (первая строка)
        headers = [h.lower().strip() for h in all_values[0]]
        
        # Находим индексы колонок
        method_idx = next((i for i, h in enumerate(headers) if 'method' in h), None)
        type_idx = next((i for i, h in enumerate(headers) if h == 'type' and 'account' not in h), None)
        account_idx = next((i for i, h in enumerate(headers) if 'account' in h), None)
        date_idx = next((i for i, h in enumerate(headers) if 'date' in h), None)
        links_idx = next((i for i, h in enumerate(headers) if 'link' in h), None)
        screenshot_idx = next((i for i, h in enumerate(headers) if 'screenshot' in h), None)
        qr_idx = next((i for i, h in enumerate(headers) if 'qr' in h), None)
        status_idx = next((i for i, h in enumerate(headers) if 'status' in h), None)
        bank_idx = next((i for i, h in enumerate(headers) if 'bank' in h), None)
        upi_id_idx = next((i for i, h in enumerate(headers) if 'upi' in h and 'id' in h), None)
        
        # Парсим строки
        providers = []
        merchant = "1win"
        merchant_domain = "1win.com"
        
        for row_idx, row in enumerate(all_values[1:], start=2):  # Пропускаем заголовки
            if not any(row):  # Пропускаем пустые строки
                continue
            
            try:
                # Извлекаем данные
                method = row[method_idx] if method_idx is not None and method_idx < len(row) else ""
                account_type = row[account_idx] if account_idx is not None and account_idx < len(row) else "FTD"
                links = row[links_idx] if links_idx is not None and links_idx < len(row) else ""
                screenshot_url = row[screenshot_idx] if screenshot_idx is not None and screenshot_idx < len(row) else ""
                qr_code = row[qr_idx] if qr_idx is not None and qr_idx < len(row) else ""
                bank = row[bank_idx] if bank_idx is not None and bank_idx < len(row) else ""
                upi_id = row[upi_id_idx] if upi_id_idx is not None and upi_id_idx < len(row) else ""
                
                # Определяем провайдера из Links, QR или Bank
                provider_entry_url = ""
                final_url = ""
                cashier_url = "https://1win.com/"
                
                if links:
                    # Обрабатываем сложные URL типа "https://1win.com/https://cai-pay.net/..."
                    # Ищем все полные URL в строке
                    import re
                    url_pattern = r'https?://[^\s]+'
                    urls = re.findall(url_pattern, links)
                    
                    if urls:
                        # Берем последний URL как final_url (обычно это URL провайдера)
                        final_url = urls[-1]
                        # Берем первый URL после 1win.com как entry_url
                        provider_entry_url = next((url for url in urls if "1win.com" not in url), final_url)
                        
                        # Если entry_url не найден, используем final_url
                        if not provider_entry_url or provider_entry_url == "https://1win.com/":
                            provider_entry_url = final_url
                    else:
                        # Если URL не найден, используем всю строку
                        provider_entry_url = links
                        final_url = links
                    
                    # Извлекаем домен провайдера из final_url
                    provider_domain = self.extract_provider_from_url(final_url)
                    
                    # Если не получилось извлечь домен или это 1win.com, пробуем из entry_url
                    if provider_domain == "unknown" or not provider_domain or provider_domain == "1win.com":
                        provider_domain = self.extract_provider_from_url(provider_entry_url)
                        
                        # Если всё еще unknown или 1win.com, используем bank или method
                        if provider_domain == "unknown" or provider_domain == "1win.com":
                            if bank:
                                provider_domain = bank.lower()
                            elif method:
                                provider_domain = method.lower()
                
                elif qr_code and qr_code.startswith("upi://"):
                    # Извлекаем домен из UPI QR кода
                    # upi://pay?pa=9680186252@okbizaxis&pn=manish&...
                    provider_entry_url = qr_code
                    final_url = qr_code
                    
                    if "@" in qr_code and "pa=" in qr_code:
                        try:
                            # Извлекаем pa=...@domain
                            upi_part = qr_code.split("pa=")[1].split("&")[0] if "pa=" in qr_code else ""
                            if "@" in upi_part:
                                provider_domain = upi_part.split("@")[1].lower()
                            else:
                                provider_domain = bank.lower() if bank else method.lower() if method else "unknown"
                        except:
                            provider_domain = bank.lower() if bank else method.lower() if method else "unknown"
                    else:
                        provider_domain = bank.lower() if bank else method.lower() if method else "unknown"
                
                else:
                    # Используем bank или method как провайдера
                    if bank:
                        provider_domain = bank.lower()
                    elif method:
                        provider_domain = method.lower()
                    else:
                        provider_domain = "unknown"
                
                # Определяем payment_method
                method_lower = method.lower() if method else ""
                if "upi" in method_lower:
                    payment_method = "UPI"
                elif "phonepe" in method_lower or "phone" in method_lower:
                    payment_method = "UPI"  # PhonePe это UPI
                elif "paytm" in method_lower or "paytm" in method_lower:
                    payment_method = "UPI"  # PayTm обычно UPI
                elif "gpay" in method_lower or "google pay" in method_lower:
                    payment_method = "UPI"  # GPay это UPI
                elif "bank" in method_lower or "transfer" in method_lower:
                    payment_method = "Bank Transfer"
                elif "wallet" in method_lower:
                    payment_method = "Wallet"
                else:
                    payment_method = "UPI"  # По умолчанию
                
                # Определяем provider_name
                if bank:
                    provider_name = bank
                elif method:
                    provider_name = method
                else:
                    provider_name = provider_domain
                
                # Определяем detected_in
                if qr_code:
                    detected_in = "qr_code"
                elif "checkouts" in links.lower() or "payment" in links.lower():
                    detected_in = "payment_page"
                else:
                    detected_in = "google_sheets_import"
                
                # Проверяем, что это данные для 1win (либо links содержит 1win.com, либо нет других мерчантов)
                is_1win_data = (
                    (links and ("1win.com" in links.lower() or "1win" in links.lower())) or
                    (not links and merchant_domain == "1win.com") or
                    True  # По умолчанию считаем что это 1win, если нет явных указаний на другой мерчант
                )
                
                if is_1win_data and provider_domain != "unknown":
                    # Если provider_domain всё еще unknown, пробуем извлечь из других источников
                    if provider_domain == "unknown":
                        if bank:
                            provider_domain = bank.lower()
                        elif qr_code and "@" in qr_code:
                            # Пробуем извлечь из QR еще раз
                            try:
                                if "pa=" in qr_code:
                                    qr_part = qr_code.split("pa=")[1].split("&")[0]
                                    if "@" in qr_part:
                                        provider_domain = qr_part.split("@")[1]
                            except:
                                pass
                    
                    # Пропускаем если всё еще unknown
                    if provider_domain == "unknown":
                        continue
                    
                    provider = {
                        "merchant": merchant,
                        "merchant_domain": merchant_domain,
                        "account_type": account_type if account_type else "FTD",
                        "provider_domain": provider_domain,
                        "provider_name": provider_name,
                        "provider_entry_url": provider_entry_url if provider_entry_url else (final_url if final_url else ""),
                        "final_url": final_url if final_url else (provider_entry_url if provider_entry_url else ""),
                        "cashier_url": cashier_url,
                        "screenshot_path": screenshot_url if screenshot_url else "",  # Храним как URL
                        "detected_in": detected_in,
                        "payment_method": payment_method,
                        "is_iframe": False,
                        "requires_otp": False,
                        "blocked_by_geo": False,
                        "captcha_present": False,
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    }
                    providers.append(provider)
            
            except Exception as e:
                print(f"⚠️  Ошибка парсинга строки {row_idx}: {e}")
                continue
        
        return providers
    
    def import_from_sheet(self, sheet_name: str = None, gid: Optional[str] = None) -> Dict:
        """
        Импорт данных из Google Sheets в БД
        
        Args:
            sheet_name: Название листа
            gid: ID листа (gid из URL)
        
        Returns:
            Словарь с результатами импорта
        """
        try:
            # Парсим данные из Google Sheets
            providers = self.parse_google_sheets_data(sheet_name=sheet_name, gid=gid)
            
            if not providers:
                return {
                    "status": "success",
                    "message": "Нет данных для импорта",
                    "imported": 0,
                    "skipped": 0,
                    "errors": 0
                }
            
            # Импортируем в БД
            imported = 0
            skipped = 0
            errors = 0
            
            for provider in providers:
                try:
                    # Проверяем, существует ли уже такая запись
                    exists = self.storage_adapter.storage.provider_exists(
                        merchant_domain=provider["merchant_domain"],
                        provider_domain=provider["provider_domain"],
                        account_type=provider.get("account_type")
                    )
                    
                    if exists:
                        skipped += 1
                        continue
                    
                    # Удаляем timestamp_utc, так как он генерируется автоматически в save_provider
                    provider_copy = {k: v for k, v in provider.items() if k != 'timestamp_utc'}
                    
                    # Сохраняем провайдера
                    saved = self.storage_adapter.storage.save_provider(**provider_copy)
                    if saved:
                        imported += 1
                    else:
                        errors += 1
                
                except Exception as e:
                    import traceback
                    error_msg = f"⚠️  Ошибка при сохранении провайдера {provider.get('provider_domain')}: {e}"
                    print(error_msg)
                    traceback.print_exc()
                    errors += 1
            
            return {
                "status": "success",
                "message": f"Импортировано {imported} провайдеров",
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
                "total": len(providers)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "imported": 0,
                "skipped": 0,
                "errors": 0
            }
