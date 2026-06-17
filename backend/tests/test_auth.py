"""
Auth API tests
"""
from datetime import datetime, timedelta

import pytest


class TestAuth:
    """Test cases for authentication endpoints"""

    def test_send_sms(self, client, test_db):
        """Test sending SMS verification code"""
        response = client.post("/api/auth/send-sms", json={
            "phone": "13900001111"
        })
        assert response.status_code == 200
        data = response.json()
        assert "code" in data or data.get("message") == "验证码发送成功"

    def test_login_success(self, client, test_db):
        """Test successful login with valid SMS code"""
        from app.models.sms import SMSCode
        from app.models.factory import Factory
        from app.models.user import User

        factory = Factory(
            factory_id="login_factory_001",
            factory_name="Login Test Factory",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)

        user = User(
            user_id="login_user_001",
            factory_id="login_factory_001",
            phone="13900002222",
            name="Login User",
            role="primary_admin",
            password_hash="hashed_password",
            status="active",
        )
        test_db.add(user)

        # Create a valid SMS code
        sms = SMSCode(
            phone="13900002222",
            code="888888",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            used=0
        )
        test_db.add(sms)
        test_db.commit()

        response = client.post("/api/auth/login", json={
            "phone": "13900002222",
            "code": "888888"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"

    def test_login_wrong_code(self, client, test_db):
        """Test login with wrong SMS code"""
        from app.models.sms import SMSCode

        # Create a valid SMS code
        sms = SMSCode(
            phone="13900003333",
            code="666666",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            used=0
        )
        test_db.add(sms)
        test_db.commit()

        response = client.post("/api/auth/login", json={
            "phone": "13900003333",
            "code": "111111"  # wrong code
        })
        assert response.status_code == 401
        assert "错误" in response.json().get("detail", "") or "无效" in response.json().get("detail", "")

    def test_get_me(self, client, test_db, auth_header):
        """Test getting current user info with valid token"""
        response = client.get("/api/auth/me", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "13800138000"
        assert data["name"] == "Test User"

    def test_password_login_demo_hash_accepts_demo_passwords_and_updates_last_login(self, client, test_db):
        """演示环境：demo_hash 用户可用约定演示密码登录，并更新 last_login。"""
        from app.models.factory import Factory
        from app.models.user import User

        factory = Factory(
            factory_id="pwd_factory_001",
            factory_name="Password Login Factory",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)
        user = User(
            user_id="pwd_user_001",
            factory_id="pwd_factory_001",
            phone="13900004444",
            name="密码登录用户",
            role="primary_admin",
            password_hash="demo_hash",
            status="active",
        )
        test_db.add(user)
        test_db.commit()

        response = client.post("/api/auth/password-login", json={
            "account": "13900004444",
            "password": "123456",
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
        test_db.refresh(user)
        assert user.last_login is not None

    def test_password_login_matches_user_id_or_name_and_plain_hash(self, client, test_db):
        """账号可匹配 user_id/name；兼容明文等于 password_hash 的演示校验。"""
        from app.models.factory import Factory
        from app.models.user import User

        factory = Factory(
            factory_id="pwd_factory_002",
            factory_name="Password Login Factory 2",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)
        user = User(
            user_id="pwd_user_002",
            factory_id="pwd_factory_002",
            phone="13900005555",
            name="明文密码用户",
            role="primary_operator",
            password_hash="plain_demo_password",
            status="active",
        )
        test_db.add(user)
        test_db.commit()

        by_user_id = client.post("/api/auth/password-login", json={
            "account": "pwd_user_002",
            "password": "plain_demo_password",
        })
        by_name = client.post("/api/auth/password-login", json={
            "account": "明文密码用户",
            "password": "plain_demo_password",
        })

        assert by_user_id.status_code == 200
        assert by_name.status_code == 200

    def test_password_login_wrong_password_keeps_failure_prompt(self, client, test_db):
        """密码登录失败时返回 401，供前端保留失败提示。"""
        from app.models.factory import Factory
        from app.models.user import User

        factory = Factory(
            factory_id="pwd_factory_003",
            factory_name="Password Login Factory 3",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)
        user = User(
            user_id="pwd_user_003",
            factory_id="pwd_factory_003",
            phone="13900006666",
            name="密码失败用户",
            role="primary_operator",
            password_hash="demo_hash",
            status="active",
        )
        test_db.add(user)
        test_db.commit()

        response = client.post("/api/auth/password-login", json={
            "account": "13900006666",
            "password": "wrong-password",
        })

        assert response.status_code == 401
        assert "账号或密码错误" in response.json().get("detail", "")
