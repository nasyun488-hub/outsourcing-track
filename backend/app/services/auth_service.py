import logging
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.sms import SMSCode

logger = logging.getLogger(__name__)

# 验证码有效期：5分钟
SMS_CODE_EXPIRE_MINUTES = 5
# 验证码长度：6位数字
SMS_CODE_LENGTH = 6


def generate_sms_code() -> str:
    """生成6位数字验证码"""
    return "".join(random.choices(string.digits, k=SMS_CODE_LENGTH))


def send_sms_mock(phone: str, code: str) -> bool:
    """
    Mock发送短信，实际只是打印到日志
    后续可对接阿里云/腾讯云SDK
    """
    logger.info(f"[MOCK SMS] 发送短信验证码 | 手机号: {phone} | 验证码: {code}")
    return True


def create_sms_code(db: Session, phone: str) -> str:
    """
    创建短信验证码
    1. 生成6位数字验证码
    2. 存储到sms_codes表
    3. Mock发送短信
    """
    code = generate_sms_code()
    expires_at = datetime.utcnow() + timedelta(minutes=SMS_CODE_EXPIRE_MINUTES)

    sms_record = SMSCode(
        phone=phone,
        code=code,
        expires_at=expires_at,
        used=0
    )
    db.add(sms_record)
    db.commit()

    # Mock发送短信
    send_sms_mock(phone, code)

    return code


def verify_sms_code(db: Session, phone: str, code: str) -> bool:
    """
    校验短信验证码
    1. 查找最新一条未使用的验证码记录
    2. 校验手机号、验证码、过期时间
    3. 标记为已使用（一次性）
    """
    sms_record = (
        db.query(SMSCode)
        .filter(
            SMSCode.phone == phone,
            SMSCode.code == code,
            SMSCode.used == 0
        )
        .order_by(SMSCode.created_at.desc())
        .first()
    )

    if not sms_record:
        logger.warning(f"[SMS VERIFY] 验证码不存在 | 手机号: {phone}")
        return False

    if datetime.utcnow() > sms_record.expires_at:
        logger.warning(f"[SMS VERIFY] 验证码已过期 | 手机号: {phone} | 过期时间: {sms_record.expires_at}")
        return False

    # 标记为已使用
    sms_record.used = 1
    db.commit()

    logger.info(f"[SMS VERIFY] 验证码校验成功 | 手机号: {phone}")
    return True


def create_access_token(user: User) -> str:
    """
    创建JWT访问令牌
    Payload包含: user_id, phone, role, factory_id
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user.user_id,
        "phone": user.phone,
        "role": user.role,
        "factory_id": user.factory_id,
        "exp": expire
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def authenticate_phone(db: Session, phone: str, code: str) -> Optional[User]:
    """
    手机号+验证码登录认证
    1. 校验验证码
    2. 查找用户
    3. 更新last_login
    4. 返回JWT
    """
    # 校验验证码
    if not verify_sms_code(db, phone, code):
        return None

    # 查找用户
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        logger.warning(f"[LOGIN] 用户不存在 | 手机号: {phone}")
        return None

    # 更新last_login
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"[LOGIN] 用户登录成功 | user_id: {user.user_id} | phone: {phone}")
    return user
