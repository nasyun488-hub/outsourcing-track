"""管理端基础 API：人员/厂家列表与轻量创建。"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.factory import Factory
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_enterprise_admin(current_user: User) -> None:
    if current_user.role != "enterprise_admin":
        raise HTTPException(status_code=403, detail="仅企业管理员可访问")


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    role: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        normalized_status = "inactive" if status == "disabled" else status
        query = query.filter(User.status == normalized_status)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (User.name.like(pattern))
            | (User.phone.like(pattern))
            | (User.user_id.like(pattern))
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": u.user_id,
                "user_id": u.user_id,
                "username": u.name,
                "name": u.name,
                "phone": u.phone,
                "role": u.role,
                "factory_id": u.factory_id,
                "factory_name": u.factory.factory_name if u.factory else "",
                "status": u.status,
            }
            for u in users
        ],
    }


@router.post("/users")
def create_user(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    role_map = {
        "factory_admin": "cooperative_admin",
        "operator": "cooperative_operator",
    }
    user_id = data.get("user_id") or f"DEMO_USER_{int(datetime.utcnow().timestamp())}"
    if db.query(User).filter(User.user_id == user_id).first():
        raise HTTPException(status_code=400, detail="用户ID已存在")
    phone = data.get("phone") or data.get("username")
    if not phone:
        raise HTTPException(status_code=400, detail="手机号必填")
    requested_role = data.get("role") or "primary_operator"
    user = User(
        user_id=user_id,
        factory_id=data.get("factory_id") or current_user.factory_id,
        phone=phone,
        name=data.get("name") or data.get("username") or phone,
        role=role_map.get(requested_role, requested_role),
        password_hash="demo_hash",
        status=data.get("status") or "active",
    )
    db.add(user)
    db.commit()
    return {"success": True, "user_id": user.user_id}


@router.put("/users/{user_id}/review")
def review_user(
    user_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "active" if data.get("approved", True) else "inactive"
    db.commit()
    return {"success": True}


@router.get("/factories")
def list_factories(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    query = db.query(Factory)
    if status:
        normalized_status = "inactive" if status == "disabled" else status
        query = query.filter(Factory.status == normalized_status)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (Factory.factory_name.like(pattern))
            | (Factory.factory_phone.like(pattern))
            | (Factory.factory_address.like(pattern))
            | (Factory.factory_id.like(pattern))
        )
    total = query.count()
    factories = query.order_by(Factory.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": f.factory_id,
                "factory_id": f.factory_id,
                "name": f.factory_name,
                "factory_name": f.factory_name,
                "contact": f.factory_address or "",
                "phone": f.factory_phone or "",
                "status": f.status,
                "factory_type": f.factory_type,
            }
            for f in factories
        ],
    }


@router.post("/factories")
def create_factory(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    factory_id = data.get("factory_id") or f"DEMO_FACTORY_{int(datetime.utcnow().timestamp())}"
    if db.query(Factory).filter(Factory.factory_id == factory_id).first():
        raise HTTPException(status_code=400, detail="厂家ID已存在")
    factory = Factory(
        factory_id=factory_id,
        factory_name=data.get("name") or data.get("factory_name") or factory_id,
        factory_type=data.get("factory_type") or "cooperative",
        factory_phone=data.get("phone") or data.get("factory_phone"),
        factory_address=data.get("contact") or data.get("factory_address"),
        status=data.get("status") or "active",
    )
    db.add(factory)
    db.commit()
    return {"success": True, "factory_id": factory.factory_id}


@router.put("/factories/{factory_id}/review")
def review_factory(
    factory_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_enterprise_admin(current_user)
    factory = db.query(Factory).filter(Factory.factory_id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="厂家不存在")
    factory.status = "active" if data.get("approved", True) else "inactive"
    db.commit()
    return {"success": True}
