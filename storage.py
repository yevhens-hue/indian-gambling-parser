# storage.py
# Хранение данных провайдеров в XLSX, SQLite и Google Sheets

import sqlite3
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd
import tldextract

# Google Sheets импорт (опционально)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("⚠️  gspread не установлен. Экспорт в Google Sheets недоступен.")


class Storage:
    def __init__(
        self, 
        db_path: str = "providers_data.db", 
        xlsx_path: str = "providers_data.xlsx",
        google_sheet_id: Optional[str] = None,
        google_credentials_path: Optional[str] = None,
        use_pool: bool = False,
        pool_size: int = 5
    ):
        self.db_path = db_path
        self.xlsx_path = xlsx_path
        self.google_sheet_id = google_sheet_id or os.getenv("GOOGLE_SHEET_ID", "1kw74QoJGHKlaLOD-FGEPRU0DXKOAh4S-8_1Bz6burFE")
        self.google_credentials_path = google_credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
        self.use_pool = use_pool
        self._db_pool = None
        
        if use_pool:
            try:
                # Пытаемся импортировать pool (доступен только в backend)
                import sys
                from pathlib import Path
                # Путь относительно storage.py: ../../web_service/backend
                current_file = Path(__file__).resolve()
                backend_path = current_file.parent.parent / "web_service" / "backend"
                if backend_path.exists():
                    sys.path.insert(0, str(backend_path))
                
                from app.services.db_pool import get_db_pool
                self._db_pool = get_db_pool(db_path=db_path, pool_size=pool_size)
            except (ImportError, Exception) as e:
                # Если pool недоступен, используем обычные соединения
                try:
                    from app.utils.logger import logger as app_logger
                    app_logger.warning(f"Connection pool недоступен, используем обычные соединения: {e}")
                except ImportError:
                    print(f"⚠️  Connection pool недоступен, используем обычные соединения: {e}")
                self.use_pool = False
        
        self.init_database()

    def init_database(self):
        """Инициализация базы данных с расширенными полями"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant TEXT NOT NULL,
                merchant_domain TEXT NOT NULL,
                account_type TEXT,
                provider_domain TEXT NOT NULL,
                provider_name TEXT,
                provider_entry_url TEXT,
                final_url TEXT,
                cashier_url TEXT,
                screenshot_path TEXT,
                detected_in TEXT,
                payment_method TEXT,
                is_iframe INTEGER DEFAULT 0,
                requires_otp INTEGER DEFAULT 0,
                blocked_by_geo INTEGER DEFAULT 0,
                captcha_present INTEGER DEFAULT 0,
                timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(merchant_domain, provider_domain, account_type)
            )
        """)
        
        # Создание индексов для ускорения запросов
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_merchant ON providers(merchant)",
            "CREATE INDEX IF NOT EXISTS idx_merchant_domain ON providers(merchant_domain)",
            "CREATE INDEX IF NOT EXISTS idx_provider_domain ON providers(provider_domain)",
            "CREATE INDEX IF NOT EXISTS idx_account_type ON providers(account_type)",
            "CREATE INDEX IF NOT EXISTS idx_payment_method ON providers(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON providers(timestamp_utc DESC)",
            "CREATE INDEX IF NOT EXISTS idx_merchant_domain_account ON providers(merchant_domain, account_type)",
            "CREATE INDEX IF NOT EXISTS idx_provider_name ON providers(provider_name) WHERE provider_name IS NOT NULL",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                # Индекс уже существует или другая ошибка - пропускаем
                print(f"⚠️  Предупреждение при создании индекса: {e}")
        
        conn.commit()
        conn.close()
        
        # Используем логирование если доступно, иначе print
        try:
            from app.utils.logger import logger as app_logger
            app_logger.info("Database initialized with indexes")
        except ImportError:
            print("✅ База данных инициализирована с индексами")

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

    def _get_connection(self):
        """Получить соединение (из pool или новое)"""
        if self.use_pool and self._db_pool:
            return self._db_pool.get_connection()
        else:
            # Fallback к обычным соединениям
            class SimpleConnection:
                def __init__(self, db_path):
                    self.conn = sqlite3.connect(db_path)
                
                def __enter__(self):
                    return self.conn
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.conn.close()
                    return False
            
            return SimpleConnection(self.db_path)
    
    def save_provider(
        self,
        merchant: str,
        merchant_domain: str,
        provider_domain: str,
        account_type: Optional[str] = None,
        provider_name: Optional[str] = None,
        provider_entry_url: Optional[str] = None,
        final_url: Optional[str] = None,
        cashier_url: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        detected_in: Optional[str] = None,
        payment_method: Optional[str] = None,
        is_iframe: bool = False,
        requires_otp: bool = False,
        blocked_by_geo: bool = False,
        captcha_present: bool = False,
    ) -> bool:
        """Сохранение данных провайдера в БД"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO providers 
                    (merchant, merchant_domain, account_type, provider_domain, provider_name,
                     provider_entry_url, final_url, cashier_url, screenshot_path, detected_in,
                     payment_method, is_iframe, requires_otp, blocked_by_geo, captcha_present,
                     timestamp_utc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    merchant, merchant_domain, account_type, provider_domain, provider_name,
                    provider_entry_url, final_url, cashier_url, screenshot_path, detected_in,
                    payment_method, int(is_iframe), int(requires_otp), int(blocked_by_geo), 
                    int(captcha_present), datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            # Используем логирование если доступно
            try:
                from app.utils.logger import logger as app_logger
                app_logger.error(f"Ошибка при сохранении в БД: {e}", exc_info=True)
            except ImportError:
                print(f"Ошибка при сохранении в БД: {e}")
            return False

    def get_all_providers(self, merchant: Optional[str] = None) -> List[Dict]:
        """Получение всех записей о провайдерах"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if merchant:
                cursor.execute("""
                    SELECT * FROM providers WHERE merchant = ? ORDER BY timestamp_utc DESC
                """, (merchant,))
            else:
                cursor.execute("SELECT * FROM providers ORDER BY timestamp_utc DESC")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_providers_paginated(
        self,
        merchant: Optional[str] = None,
        provider_domain: Optional[str] = None,
        account_type: Optional[str] = None,
        payment_method: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "timestamp_utc",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Получение провайдеров с фильтрацией и пагинацией на уровне SQL.
        
        Оптимизированный метод, который выполняет фильтрацию, сортировку и 
        пагинацию прямо в SQL запросе вместо Python.
        
        Returns:
            Dict с items, total, skip, limit, has_more
        """
        # Валидация sort_by для предотвращения SQL injection
        allowed_sort_fields = {
            'id', 'merchant', 'merchant_domain', 'provider_domain', 'provider_name',
            'account_type', 'payment_method', 'timestamp_utc', 'detected_in'
        }
        if sort_by not in allowed_sort_fields:
            sort_by = 'timestamp_utc'
        
        # Валидация sort_order
        sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Строим WHERE clause
            conditions = []
            params = []
            
            if merchant:
                conditions.append("merchant = ?")
                params.append(merchant)
            
            if provider_domain:
                conditions.append("provider_domain LIKE ?")
                params.append(f"%{provider_domain}%")
            
            if account_type:
                conditions.append("account_type = ?")
                params.append(account_type)
            
            if payment_method:
                conditions.append("payment_method = ?")
                params.append(payment_method)
            
            if search:
                search_pattern = f"%{search}%"
                conditions.append("""
                    (merchant LIKE ? OR merchant_domain LIKE ? OR provider_domain LIKE ? 
                     OR provider_name LIKE ? OR detected_in LIKE ? OR payment_method LIKE ?
                     OR provider_entry_url LIKE ? OR final_url LIKE ?)
                """)
                params.extend([search_pattern] * 8)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Подсчёт общего количества
            count_query = f"SELECT COUNT(*) FROM providers WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Основной запрос с пагинацией
            query = f"""
                SELECT * FROM providers 
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [limit, skip])
            
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            
            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(items)) < total
            }

    def export_to_xlsx(self, output_path: Optional[str] = None):
        """Экспорт данных в XLSX и Google Sheets"""
        if output_path is None:
            output_path = self.xlsx_path
        
        rows = self.get_all_providers()
        if not rows:
            print("Нет данных для экспорта")
            return
        
        # Преобразуем в DataFrame
        df = pd.DataFrame(rows)
        
        # Удаляем служебные колонки
        df = df.drop(columns=['id'], errors='ignore')
        
        # Сохраняем в XLSX
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"✓ Данные экспортированы в {output_path} ({len(rows)} записей)")
        
        # Экспорт в Google Sheets
        self.export_to_google_sheets(df)
    
    def export_to_google_sheets(self, df: pd.DataFrame):
        """Экспорт данных в Google Sheets - добавляет новые строки вместо перезаписи"""
        if not GOOGLE_SHEETS_AVAILABLE:
            print("⚠️  Google Sheets API не доступен (gspread не установлен)")
            return
        
        if not self.google_sheet_id:
            print("⚠️  Google Sheet ID не указан")
            return
        
        try:
            # Проверяем наличие файла с credentials
            if not os.path.exists(self.google_credentials_path):
                print(f"⚠️  Файл с credentials не найден: {self.google_credentials_path}")
                print("   Создайте Service Account в Google Cloud Console и скачайте JSON ключ")
                return
            
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
            worksheet = sheet.sheet1  # Используем первый лист
            
            # Получаем существующие данные
            try:
                existing_data = worksheet.get_all_values()
            except Exception as e:
                print(f"  ⚠️  Не удалось прочитать существующие данные: {e}")
                existing_data = []
            
            # Определяем заголовки
            if len(existing_data) == 0:
                # Если лист пустой - добавляем заголовки
                headers = df.columns.tolist()
                worksheet.append_row(headers, value_input_option='RAW')
                print(f"  → Добавлены заголовки: {', '.join(headers)}")
                existing_data = [headers]
            else:
                headers = existing_data[0]
                # Проверяем соответствие заголовков
                if headers != df.columns.tolist():
                    print(f"  ⚠️  Заголовки в Google Sheets не совпадают с данными")
                    print(f"  Google Sheets: {headers}")
                    print(f"  Данные: {df.columns.tolist()}")
                    # Продолжаем работу, но можем пропустить некоторые столбцы
            
            # Создаём множество существующих записей для проверки дубликатов
            # Используем комбинацию merchant_domain + provider_domain + account_type как ключ
            existing_keys = set()
            if len(existing_data) > 1:
                merchant_idx = headers.index('merchant_domain') if 'merchant_domain' in headers else -1
                provider_idx = headers.index('provider_domain') if 'provider_domain' in headers else -1
                account_idx = headers.index('account_type') if 'account_type' in headers else -1
                
                for row in existing_data[1:]:  # Пропускаем заголовки
                    if merchant_idx >= 0 and provider_idx >= 0:
                        merchant = row[merchant_idx] if merchant_idx < len(row) else ""
                        provider = row[provider_idx] if provider_idx < len(row) else ""
                        account = row[account_idx] if account_idx >= 0 and account_idx < len(row) else None
                        key = (merchant, provider, account)
                        existing_keys.add(key)
            
            # Подготавливаем новые строки для добавления
            new_rows = []
            merchant_col = df.columns.get_loc('merchant_domain') if 'merchant_domain' in df.columns else -1
            provider_col = df.columns.get_loc('provider_domain') if 'provider_domain' in df.columns else -1
            account_col = df.columns.get_loc('account_type') if 'account_type' in df.columns else -1
            
            for _, row in df.iterrows():
                # Проверяем, не является ли запись дубликатом
                if merchant_col >= 0 and provider_col >= 0:
                    merchant = str(row.iloc[merchant_col])
                    provider = str(row.iloc[provider_col])
                    account = str(row.iloc[account_col]) if account_col >= 0 else None
                    key = (merchant, provider, account)
                    
                    if key in existing_keys:
                        continue  # Пропускаем дубликаты
                
                # Преобразуем строку DataFrame в список
                row_list = [str(val) if pd.notna(val) else "" for val in row.values]
                new_rows.append(row_list)
            
            # Добавляем новые строки
            if new_rows:
                worksheet.append_rows(new_rows, value_input_option='RAW')
                print(f"✓ Добавлено {len(new_rows)} новых строк в Google Sheets")
                print(f"  Ссылка: https://docs.google.com/spreadsheets/d/{self.google_sheet_id}")
            else:
                print(f"  → Все записи уже существуют в Google Sheets, новые строки не добавлены")
                
        except FileNotFoundError:
            print(f"❌ Файл credentials не найден: {self.google_credentials_path}")
            print("   Создайте Service Account в Google Cloud Console")
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Google Таблица не найдена. Проверьте ID: {self.google_sheet_id}")
            print("   Убедитесь, что Service Account имеет доступ к таблице")
        except gspread.exceptions.APIError as e:
            print(f"❌ Ошибка Google Sheets API: {e}")
        except Exception as e:
            print(f"❌ Ошибка при экспорте в Google Sheets: {e}")
            import traceback
            traceback.print_exc()
    
    def append_deposit_result(self, merchant: str, timestamp: str, final_url: str, screenshot_path: str):
        """Добавляет строку deposit result в Google Sheets (для olymptrade)"""
        if not GOOGLE_SHEETS_AVAILABLE:
            print("⚠️  Google Sheets API не доступен")
            return
        
        if not self.google_sheet_id:
            print("⚠️  Google Sheet ID не указан")
            return
        
        try:
            if not os.path.exists(self.google_credentials_path):
                print(f"⚠️  Файл с credentials не найден: {self.google_credentials_path}")
                return
            
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
            
            # Используем первый лист (можно изменить на нужный по gid)
            worksheet = sheet.sheet1
            
            # Подготавливаем строку для добавления: merchant, timestamp, final_url, screenshot_path
            row = [merchant, timestamp, final_url, screenshot_path]
            
            # Добавляем строку
            worksheet.append_row(row, value_input_option='RAW')
            print(f"✓ Добавлена строка deposit result в Google Sheets")
            print(f"  Ссылка: https://docs.google.com/spreadsheets/d/{self.google_sheet_id}")
            
        except Exception as e:
            print(f"⚠️  Ошибка при добавлении deposit result в Google Sheets: {e}")
            import traceback
            traceback.print_exc()

    def provider_exists(self, merchant_domain: str, provider_domain: str, account_type: Optional[str] = None) -> bool:
        """Проверка существования записи"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if account_type:
                cursor.execute("""
                    SELECT COUNT(*) FROM providers 
                    WHERE merchant_domain = ? AND provider_domain = ? AND account_type = ?
                """, (merchant_domain, provider_domain, account_type))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM providers 
                    WHERE merchant_domain = ? AND provider_domain = ?
                """, (merchant_domain, provider_domain))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def delete_provider(self, provider_id: int) -> bool:
        """Удаление провайдера по ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            try:
                from app.utils.logger import logger as app_logger
                app_logger.error(f"Ошибка при удалении провайдера {provider_id}: {e}", exc_info=True)
            except ImportError:
                print(f"Ошибка при удалении провайдера {provider_id}: {e}")
            return False
    
    def batch_delete_providers(self, provider_ids: List[int]) -> Dict[str, Any]:
        """
        Массовое удаление провайдеров
        
        Returns:
            dict с ключами: deleted_count, not_found_ids
        """
        deleted_count = 0
        not_found_ids = []
        
        for provider_id in provider_ids:
            if self.delete_provider(provider_id):
                deleted_count += 1
            else:
                not_found_ids.append(provider_id)
        
        return {
            "deleted_count": deleted_count,
            "not_found_ids": not_found_ids
        }

