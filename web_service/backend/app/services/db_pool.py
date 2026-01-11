"""Connection Pool для SQLite"""
import sqlite3
import threading
import queue
from contextlib import contextmanager
from typing import Optional
import os


class SQLitePool:
    """
    Простой connection pool для SQLite
    
    ВАЖНО: SQLite не полностью поддерживает множественные соединения из-за file locking.
    Этот pool помогает переиспользовать соединения, но не решает проблему concurrency полностью.
    Для production рекомендуется использовать PostgreSQL.
    """
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: float = 5.0):
        """
        Инициализация pool
        
        Args:
            db_path: Путь к файлу БД
            pool_size: Размер pool (количество соединений)
            timeout: Таймаут получения соединения из pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool: queue.Queue = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._created_connections = 0
        
        # Инициализация pool
        self._initialize_pool()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Создание нового соединения"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.timeout
        )
        conn.row_factory = sqlite3.Row  # Возвращает dict-like объекты
        self._created_connections += 1
        return conn
    
    def _initialize_pool(self):
        """Инициализация pool соединениями"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """
        Получить соединение из pool (context manager)
        
        Использование:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM providers")
                results = cursor.fetchall()
        """
        conn = None
        try:
            # Получаем соединение из pool (с таймаутом)
            try:
                conn = self.pool.get(timeout=self.timeout)
            except queue.Empty:
                # Если pool пуст, создаем новое соединение
                conn = self._create_connection()
            
            yield conn
            
        except Exception as e:
            # При ошибке закрываем соединение и создаем новое
            if conn:
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_connection()
            raise
        finally:
            # Возвращаем соединение в pool (если оно валидное)
            if conn:
                try:
                    # Проверяем, что соединение не закрыто
                    conn.execute("SELECT 1")
                    self.pool.put(conn, block=False)
                except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                    # Если соединение невалидное, создаем новое
                    try:
                        conn.close()
                    except:
                        pass
                    new_conn = self._create_connection()
                    try:
                        self.pool.put(new_conn, block=False)
                    except queue.Full:
                        # Pool полон, закрываем соединение
                        new_conn.close()
    
    def close_all(self):
        """Закрыть все соединения в pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except (queue.Empty, sqlite3.Error):
                pass
    
    def get_stats(self) -> dict:
        """Получить статистику pool"""
        return {
            "pool_size": self.pool_size,
            "available_connections": self.pool.qsize(),
            "created_connections": self._created_connections,
        }


# Глобальный pool (будет инициализирован при первом использовании)
_db_pool: Optional[SQLitePool] = None
_pool_lock = threading.Lock()


def get_db_pool(db_path: str, pool_size: int = 5) -> SQLitePool:
    """
    Получить глобальный DB pool (singleton)
    
    Args:
        db_path: Путь к БД
        pool_size: Размер pool
    
    Returns:
        SQLitePool instance
    """
    global _db_pool
    
    with _pool_lock:
        if _db_pool is None:
            _db_pool = SQLitePool(db_path=db_path, pool_size=pool_size)
        return _db_pool


def close_db_pool():
    """Закрыть глобальный pool (для cleanup)"""
    global _db_pool
    with _pool_lock:
        if _db_pool:
            _db_pool.close_all()
            _db_pool = None
