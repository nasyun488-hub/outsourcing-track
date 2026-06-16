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
