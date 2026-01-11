"""API endpoints для авторизации"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.auth.auth import (
    authenticate_user,
    create_access_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    username: str
    role: str


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Авторизация пользователя
    
    По умолчанию:
    - username: admin
    - password: admin123
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInfo)
async def read_users_me(current_user: str = Depends(verify_token)):
    """Получить информацию о текущем пользователе"""
    from app.auth.auth import get_users_db
    users_db = get_users_db()
    user = users_db.get(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "role": user["role"]}
