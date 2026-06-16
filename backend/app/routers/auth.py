from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    SmsCodeRequest,
    PhoneLoginRequest,
    TokenResponse,
    UserResponse
)
from app.services.auth_service import (
    create_sms_code,
    authenticate_phone,
    create_access_token
)
from app.middleware.auth import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/send-sms", summary="发送短信验证码")
async def send_sms(request: SmsCodeRequest, db: Session = Depends(get_db)):
    """
    发送短信验证码
    - 生成6位数字验证码
    - 存储到数据库（5分钟有效期）
    - Mock发送短信（打印到日志）
    """
    code = create_sms_code(db, request.phone)
    return {"message": "验证码发送成功", "code": code}  # 调试时返回code，生产环境应移除


@router.post("/login", response_model=TokenResponse, summary="手机号+验证码登录")
async def login(request: PhoneLoginRequest, db: Session = Depends(get_db)):
    """
    手机号+验证码登录
    - 校验验证码
    - 查找用户
    - 更新last_login
    - 返回JWT Token
    """
    user = authenticate_phone(db, request.phone, request.code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或验证码错误"
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未启用或待审核"
        )

    access_token = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    需要携带有效的JWT Token
    """
    return current_user
