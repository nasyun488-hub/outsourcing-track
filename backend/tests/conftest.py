"""
pytest configuration and fixtures for backend testing
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.config import settings


# Test database URL - SQLite in-memory
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database tables and provide a test database session"""
    # Import all models to ensure they're registered with Base
    from app.models import (
        Factory, User, Order, Process,
        ProcessRecord, ReceiveBatch, ShipBatch, ReturnRecord,
        ActionLog, Notification
    )
    from app.models.sms import SMSCode

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database"""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Mock the JWT SECRET_KEY to a fixed test value
    original_secret_key = settings.SECRET_KEY
    settings.SECRET_KEY = "test-secret-key-for-testing-only-123456"

    with TestClient(app) as c:
        yield c

    # Restore original settings
    settings.SECRET_KEY = original_secret_key
    app.dependency_overrides.clear()


@pytest.fixture
def auth_header(client, test_db) -> dict:
    """
    Create a test user, send SMS, login and return auth header.
    The token is the user_id (simplified for testing).
    """
    from app.models.user import User
    from app.models.factory import Factory
    from app.models.sms import SMSCode
    # Create a test factory first
    factory = test_db.query(Factory).filter(Factory.factory_id == "factory_001").first()
    if not factory:
        factory = Factory(
            factory_id="factory_001",
            factory_name="Test Factory",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)
        test_db.commit()

    # Create a test user
    test_user = test_db.query(User).filter(User.user_id == "user_001").first()
    if not test_user:
        test_user = User(
            user_id="user_001",
            factory_id="factory_001",
            phone="13800138000",
            name="Test User",
            role="primary_admin",
            password_hash="hashed_password",
            status="active",
        )
        test_db.add(test_user)
        test_db.commit()

    # Create SMS code for login
    sms_code = SMSCode(
        phone="13800138000",
        code="123456",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        used=0
    )
    test_db.add(sms_code)
    test_db.commit()

    # Login to get token
    response = client.post("/api/auth/login", json={
        "phone": "13800138000",
        "code": "123456"
    })
    assert response.status_code == 200, f"Login failed: {response.json()}"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_factory(test_db):
    """Create a test factory"""
    from app.models.factory import Factory

    existing = test_db.query(Factory).filter(Factory.factory_id == "factory_001").first()
    if existing:
        return existing

    factory = Factory(
        factory_id="factory_001",
        factory_name="Test Factory",
        factory_type="primary",
        status="active",
    )
    test_db.add(factory)
    test_db.commit()
    test_db.refresh(factory)
    return factory


@pytest.fixture
def test_user(test_db, test_factory):
    """Create a test user"""
    from app.models.user import User

    user = User(
        user_id="user_001",
        factory_id="factory_001",
        phone="13800138000",
        name="Test User",
        role="primary_admin",
        password_hash="hashed_password",
        status="active",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_order(test_db, test_factory):
    """Create a test order"""
    from app.models.order import Order, OrderStatus

    order = Order(
        order_id="order_001",
        primary_factory_id="factory_001",
        order_status=OrderStatus.PENDING,
        total_qty=100,
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    return order


@pytest.fixture
def test_processes(test_db, test_order, test_factory):
    """Create test processes for the order"""
    from app.models.process import Process

    # Process 1 - primary factory
    process1 = Process(
        process_id="proc_001",
        order_id="order_001",
        process_seq="010",
        process_name="Process 1",
        factory_id="factory_001",
        process_order=1,
    )
    test_db.add(process1)

    # Process 2 - same factory for simplicity
    process2 = Process(
        process_id="proc_002",
        order_id="order_001",
        process_seq="020",
        process_name="Process 2",
        factory_id="factory_001",
        process_order=2,
    )
    test_db.add(process2)
    test_db.commit()

    return [process1, process2]


@pytest.fixture
def test_record(test_db, test_order, test_processes):
    """Create a test process record"""
    from app.models.record import ProcessRecord

    record = ProcessRecord(
        record_id="record_001",
        order_id="order_001",
        process_id="proc_001",
        factory_id="factory_001",
        record_status="pending",
        lock_type="none",
        total_receive_qty=0,
        total_ship_qty=0,
    )
    test_db.add(record)
    test_db.commit()
    test_db.refresh(record)
    return record
