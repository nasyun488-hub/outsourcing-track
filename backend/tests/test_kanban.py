"""
Kanban看板 API tests
Tests order list and statistics endpoints
"""
import pytest
from datetime import datetime


class _FakeDiffResult:
    def __init__(self, diff_hours=0):
        self.diff_hours = diff_hours

    def fetchone(self):
        return (self.diff_hours,)


def _disable_mysql_timediff_for_sqlite(monkeypatch, db, diff_hours=0):
    """KanbanService 使用 MySQL TIMESTAMPDIFF；单测用 SQLite 时固定返回指定小时数。"""
    original_execute = db.execute

    def execute_with_timediff_stub(statement, *args, **kwargs):
        if "TIMESTAMPDIFF" in str(statement):
            return _FakeDiffResult(diff_hours)
        return original_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db, "execute", execute_with_timediff_stub)


def _create_kanban_permission_sample(test_db):
    """A厂第1道已发完，B厂第2道待接收，用于验证看板建议不可跨厂。"""
    from app.models.factory import Factory
    from app.models.order import Order, OrderStatus
    from app.models.process import Process
    from app.models.record import ProcessRecord
    from app.models.user import User

    factory_a = Factory(factory_id="factory_A", factory_name="A厂", factory_type="primary", status="active")
    factory_b = Factory(factory_id="factory_B", factory_name="B厂", factory_type="cooperative", status="active")
    test_db.add_all([factory_a, factory_b])

    user_a = User(user_id="user_A", factory_id="factory_A", phone="13800000001", name="A厂操作员", role="primary_operator", password_hash="demo_hash", status="active")
    user_b = User(user_id="user_B", factory_id="factory_B", phone="13800000002", name="B厂操作员", role="cooperative_operator", password_hash="demo_hash", status="active")
    test_db.add_all([user_a, user_b])

    order = Order(order_id="kanban_permission_order", primary_factory_id="factory_A", order_status=OrderStatus.IN_PROGRESS, total_qty=60)
    test_db.add(order)

    proc1 = Process(process_id="proc_A_1", order_id=order.order_id, process_seq="010", process_name="A厂首道", factory_id="factory_A", process_order=1)
    proc2 = Process(process_id="proc_B_2", order_id=order.order_id, process_seq="020", process_name="B厂二道", factory_id="factory_B", process_order=2)
    proc3 = Process(process_id="proc_A_3", order_id=order.order_id, process_seq="030", process_name="A厂末道", factory_id="factory_A", process_order=3)
    test_db.add_all([proc1, proc2, proc3])

    rec1 = ProcessRecord(record_id="record_A_1", order_id=order.order_id, process_id=proc1.process_id, factory_id="factory_A", record_status="shipped", lock_type="none", total_receive_qty=60, total_ship_qty=60, created_at=datetime.utcnow())
    rec2 = ProcessRecord(record_id="record_B_2", order_id=order.order_id, process_id=proc2.process_id, factory_id="factory_B", record_status="pending", lock_type="none", total_receive_qty=0, total_ship_qty=0, created_at=datetime.utcnow())
    rec3 = ProcessRecord(record_id="record_A_3", order_id=order.order_id, process_id=proc3.process_id, factory_id="factory_A", record_status="pending", lock_type="none", total_receive_qty=0, total_ship_qty=0, created_at=datetime.utcnow())
    test_db.add_all([rec1, rec2, rec3])
    test_db.commit()
    return order, user_a, user_b


class TestKanban:
    """Test cases for kanban看板 endpoints"""

    def test_order_list(self, client, test_db, auth_header):
        """
        Test getting order list:
        1. Create test orders with different statuses
        2. Call /api/kanban/orders
        3. Assert pagination works
        """
        from app.models.order import Order, OrderStatus
        from app.models.factory import Factory

        # Create factory first
        factory = Factory(
            factory_id="factory_k1",
            factory_name="Kanban Test Factory",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)

        # Create multiple orders
        for i in range(5):
            order = Order(
                order_id=f"kanban_order_{i}",
                primary_factory_id="factory_001",
                total_qty=100 + i * 10,
                order_status=OrderStatus.PENDING if i % 2 == 0 else OrderStatus.IN_PROGRESS,
            )
            test_db.add(order)
        test_db.commit()

        # Get order list
        response = client.get("/api/kanban/orders", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 5

    def test_stats(self, client, test_db, auth_header):
        """
        Test kanban statistics:
        1. Create orders with various statuses (pending, in_progress, completed)
        2. Call /api/kanban/stats
        3. Assert counts match
        """
        from app.models.order import Order, OrderStatus
        from app.models.factory import Factory

        # Create factory
        factory = Factory(
            factory_id="factory_stats",
            factory_name="Stats Test Factory",
            factory_type="primary",
            status="active",
        )
        test_db.add(factory)

        # Create orders with different statuses
        statuses = [
            OrderStatus.PENDING,
            OrderStatus.PENDING,
            OrderStatus.IN_PROGRESS,
            OrderStatus.IN_PROGRESS,
            OrderStatus.IN_PROGRESS,
            OrderStatus.COMPLETED,
            OrderStatus.COMPLETED,
            OrderStatus.COMPLETED,
            OrderStatus.COMPLETED,
        ]

        for i, status in enumerate(statuses):
            order = Order(
                order_id=f"stats_order_{i}",
                primary_factory_id="factory_001",
                total_qty=100,
                order_status=status,
            )
            test_db.add(order)
        test_db.commit()

        # Get stats
        response = client.get("/api/kanban/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        
        # Should have counts for: total, pending, in_progress, completed, overdue_count
        assert "total" in data
        assert "pending" in data
        assert "in_progress" in data
        assert "completed" in data
        assert "overdue_count" in data
        
        # Verify counts
        assert data["total"] >= len(statuses)
        assert data["pending"] >= 2
        assert data["in_progress"] >= 3
        assert data["completed"] >= 4

    def test_processes_kanban_marks_only_own_factory_actions_operable(self, test_db, monkeypatch):
        """A厂可看到相邻B厂工序数量，但不能被建议/按钮引导去操作B厂。"""
        from app.services.kanban_service import KanbanService

        _disable_mysql_timediff_for_sqlite(monkeypatch, test_db)
        order, user_a, _ = _create_kanban_permission_sample(test_db)

        result = KanbanService(test_db).get_processes_kanban(order.order_id, current_user=user_a)
        by_record = {item.record_id: item for item in result.items}

        assert by_record["record_A_1"].factory_id == "factory_A"
        assert by_record["record_A_1"].can_receive is False
        assert by_record["record_A_1"].can_ship is False
        assert by_record["record_A_1"].next_action is None

        assert by_record["record_B_2"].factory_id == "factory_B"
        assert by_record["record_B_2"].available_receive_qty == 60
        assert by_record["record_B_2"].can_receive is False
        assert by_record["record_B_2"].can_ship is False
        assert by_record["record_B_2"].next_action is None
        assert by_record["record_B_2"].disabled_reason == "仅可查看相邻工序，无权操作该厂家工序"

    def test_processes_kanban_allows_own_factory_receive_action(self, test_db, monkeypatch):
        """B厂用户查看同一订单时，第2道应明确给出可接收动作。"""
        from app.services.kanban_service import KanbanService

        _disable_mysql_timediff_for_sqlite(monkeypatch, test_db)
        order, _, user_b = _create_kanban_permission_sample(test_db)

        result = KanbanService(test_db).get_processes_kanban(order.order_id, current_user=user_b)
        record_b = {item.record_id: item for item in result.items}["record_B_2"]

        assert record_b.factory_id == "factory_B"
        assert record_b.available_receive_qty == 60
        assert record_b.can_receive is True
        assert record_b.can_ship is False
        assert record_b.next_action == "receive"
        assert record_b.disabled_reason is None

    def test_processes_kanban_exposes_bottleneck_and_risk_level(self, test_db, monkeypatch):
        """看板应给出当前卡点、风险等级和风险原因，前端不再临时猜测。"""
        from app.services.kanban_service import KanbanService

        _disable_mysql_timediff_for_sqlite(monkeypatch, test_db, diff_hours=72)
        order, _, user_b = _create_kanban_permission_sample(test_db)

        result = KanbanService(test_db).get_processes_kanban(order.order_id, current_user=user_b)

        assert result.current_bottleneck_record_id == "record_B_2"
        assert result.risk_level == "high"
        assert "二道" in result.risk_reason or "B厂" in result.risk_reason
        by_record = {item.record_id: item for item in result.items}
        record_b = by_record["record_B_2"]
        record_a3 = by_record["record_A_3"]
        assert record_b.is_bottleneck is True
        assert record_b.risk_level == "high"
        assert record_b.risk_reason
        assert record_a3.is_bottleneck is False
        assert record_a3.risk_level in {"normal", "medium"}

    def test_processes_kanban_creates_idempotent_risk_notification_for_owner(self, test_db, monkeypatch):
        """超期卡点刷新看板时，应只给对应厂家未读用户生成一条幂等风险提醒。"""
        from app.models.notification import Notification
        from app.services.kanban_service import KanbanService

        _disable_mysql_timediff_for_sqlite(monkeypatch, test_db, diff_hours=72)
        order, _, user_b = _create_kanban_permission_sample(test_db)

        service = KanbanService(test_db)
        service.get_processes_kanban(order.order_id, current_user=user_b)
        service.get_processes_kanban(order.order_id, current_user=user_b)

        notifications = test_db.query(Notification).filter(
            Notification.user_id == user_b.user_id,
            Notification.related_id == order.order_id,
            Notification.related_type == "order",
            Notification.is_read == "0",
        ).all()
        assert len(notifications) == 1
        assert "风险" in notifications[0].title or "超期" in notifications[0].title
        assert notifications[0].jump_url == f"/kanban/{order.order_id}"
