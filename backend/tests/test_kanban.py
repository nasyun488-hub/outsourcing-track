"""
Kanban看板 API tests
Tests order list and statistics endpoints
"""
import pytest


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
                primary_factory_id="factory_k1",
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
                primary_factory_id="factory_stats",
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
