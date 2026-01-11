"""Сервис аудит-лога (история изменений)"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from app.utils.logger import logger
import sqlite3
import json
import os
from pathlib import Path


class AuditLogService:
    """Сервис для ведения истории изменений"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Инициализация audit log service
        
        Args:
            db_path: Путь к БД (если None, используется та же БД что и для providers)
        """
        if db_path is None:
            # Используем ту же БД
            from app.config import DB_PATH
            db_path = DB_PATH
        
        self.db_path = db_path
        self.init_audit_table()
    
    def init_audit_table(self) -> None:
        """Инициализация таблицы audit_log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    action TEXT NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для быстрого поиска
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp_utc DESC)",
                "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)",
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
            conn.close()
            
            logger.debug("Audit log table initialized")
        except Exception as e:
            logger.error(f"Error initializing audit log table: {e}", exc_info=True)
    
    def log_action(
        self,
        table_name: str,
        action: str,
        record_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Записать действие в audit log
        
        Args:
            table_name: Название таблицы
            action: Действие (INSERT, UPDATE, DELETE)
            record_id: ID записи
            old_values: Старые значения (для UPDATE/DELETE)
            new_values: Новые значения (для INSERT/UPDATE)
            user_id: ID пользователя
            ip_address: IP адрес
            user_agent: User-Agent
        
        Returns:
            True если успешно, False иначе
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_log 
                (table_name, record_id, action, old_values, new_values, user_id, ip_address, user_agent, timestamp_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                table_name,
                record_id,
                action,
                json.dumps(old_values, ensure_ascii=False) if old_values else None,
                json.dumps(new_values, ensure_ascii=False) if new_values else None,
                user_id,
                ip_address,
                user_agent,
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Audit log: {action} on {table_name}:{record_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging audit action: {e}", exc_info=True)
            return False
    
    def get_audit_log(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получить записи из audit log
        
        Args:
            table_name: Фильтр по таблице
            record_id: Фильтр по ID записи
            action: Фильтр по действию
            limit: Максимум записей
        
        Returns:
            Список записей audit log
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)
            
            if record_id is not None:
                query += " AND record_id = ?"
                params.append(record_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY timestamp_utc DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                item = dict(row)
                # Парсим JSON значения
                if item.get('old_values'):
                    try:
                        item['old_values'] = json.loads(item['old_values'])
                    except:
                        pass
                if item.get('new_values'):
                    try:
                        item['new_values'] = json.loads(item['new_values'])
                    except:
                        pass
                result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"Error getting audit log: {e}", exc_info=True)
            return []


# Глобальный экземпляр
_audit_log_service: Optional[AuditLogService] = None


def get_audit_log_service() -> AuditLogService:
    """Получить глобальный audit log service"""
    global _audit_log_service
    if _audit_log_service is None:
        _audit_log_service = AuditLogService()
    return _audit_log_service
