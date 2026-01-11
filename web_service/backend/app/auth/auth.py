"""Модуль авторизации (JWT)"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Настройки безопасности
SECRET_KEY = "your-secret-key-change-in-production"  # В продакшене использовать переменную окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка JWT токена"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Простой in-memory хранилище пользователей (в продакшене использовать БД)
# Используем предвычисленный хеш для избежания проблем с импортом
# В production используйте переменные окружения или БД
_ADMIN_PASSWORD_HASH = None

def _get_admin_hash():
    """Ленивое вычисление хеша пароля admin"""
    global _ADMIN_PASSWORD_HASH
    if _ADMIN_PASSWORD_HASH is None:
        _ADMIN_PASSWORD_HASH = get_password_hash("admin123")
    return _ADMIN_PASSWORD_HASH

def get_users_db():
    """Получить БД пользователей"""
    return {
        "admin": {
            "username": "admin",
            "hashed_password": _get_admin_hash(),
            "role": "admin"
        }
    }


def authenticate_user(username: str, password: str):
    """Аутентификация пользователя"""
    user = USERS_DB.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user
