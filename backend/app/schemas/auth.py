from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SmsCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., min_length=11, max_length=20, description="手机号")


class PhoneLoginRequest(BaseModel):
    """手机号+验证码登录请求"""
    phone: str = Field(..., min_length=11, max_length=20, description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


class PasswordLoginRequest(BaseModel):
    """手机号/账号+密码登录请求"""
    account: str = Field(..., min_length=1, max_length=64, description="手机号、用户ID或姓名")
    password: str = Field(..., min_length=1, max_length=256, description="密码")


class TokenResponse(BaseModel):
    """登录成功返回的Token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="过期时间（秒）")


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: str
    factory_id: str
    phone: str
    name: str
    role: str
    status: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
