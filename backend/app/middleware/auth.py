from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


class TokenPayload:
    """JWT Token载荷"""
    def __init__(self, user_id: str, phone: str, role: str, factory_id: str):
        self.user_id = user_id
        self.phone = phone
        self.role = role
        self.factory_id = factory_id


def verify_token(token: str) -> Optional[TokenPayload]:
    """
    验证JWT Token
    返回TokenPayload或None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(
            user_id=payload.get("user_id"),
            phone=payload.get("phone"),
            role=payload.get("role"),
            factory_id=payload.get("factory_id")
        )
    except JWTError as e:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI依赖：获取当前登录用户
    从JWT Token中解析user_id，查询数据库返回用户对象
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == payload.user_id).first()
    if user is None or user.status != "active":
        raise credentials_exception
    return user
