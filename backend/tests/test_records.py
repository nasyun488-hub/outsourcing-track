"""
Record流转记录 API tests
Tests the core flow: receive -> ship -> return
"""
import pytest


class TestRecords:
    """Test cases for record流转 endpoints"""

    def test_receive_flow(self, client, test_db, auth_header, test_factory, test_order, test_processes):
        """
        Test complete receive flow:
        1. Create process record
        2. Ship from previous process (since first process needs previous to have shipped)
        3. But for simplicity - the first process doesn't need previous shipped
        Actually need to setup chain properly
        """
        from app.models.record import ProcessRecord, ShipBatch
        from app.models.process import Process

        # Create ship batch for the first process (to allow receive)
        # First need to create the process record and ship to it
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

        # Actually, since proc_001 has no previous process, we can receive directly
        response = client.post("/api/records/receive", 
            headers=auth_header,
            json={
                "record_id": "record_001",
                "receive_qty": 50,
                "receive_time": None
            }
        )
        
        # The response should be successful
        assert response.status_code == 200, f"Receive failed: {response.json()}"
        data = response.json()
        assert data["success"] is True
        assert data["record"]["record_status"] == "received"
        assert data["record"]["total_receive_qty"] == 50

    def test_ship_flow(self, client, test_db, auth_header, test_factory, test_order, test_processes):
        """
        Test ship flow after receiving:
        1. Create record and receive some quantity
        2. Ship the received quantity
        3. Assert status becomes 'shipped'
        """
        from app.models.record import ProcessRecord, ReceiveBatch

        # Create process record with some received quantity
        record = ProcessRecord(
            record_id="record_002",
            order_id="order_001",
            process_id="proc_001",
            factory_id="factory_001",
            record_status="received",
            lock_type="entry_lock",
            total_receive_qty=80,
            total_ship_qty=0,
        )
        test_db.add(record)
        test_db.commit()

        # Now ship
        response = client.post("/api/records/ship",
            headers=auth_header,
            json={
                "record_id": "record_002",
                "ship_qty": 80,
                "ship_time": None
            }
        )
        
        assert response.status_code == 200, f"Ship failed: {response.json()}"
        data = response.json()
        assert data["success"] is True
        assert data["record"]["record_status"] == "shipped"
        assert data["record"]["total_ship_qty"] == 80

    def test_partial_receive(self, client, test_db, auth_header, test_factory, test_order, test_processes):
        """
        Test partial receive (multiple batches):
        1. First receive 30 units
        2. Second receive 40 units  
        3. Assert total is accumulated (70)
        """
        from app.models.record import ProcessRecord

        # Create process record
        record = ProcessRecord(
            record_id="record_003",
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

        # First receive
        response1 = client.post("/api/records/receive",
            headers=auth_header,
            json={
                "record_id": "record_003",
                "receive_qty": 30,
                "receive_time": None
            }
        )
        assert response1.status_code == 200, f"First receive failed: {response1.json()}"
        assert response1.json()["record"]["total_receive_qty"] == 30

        # Second receive
        response2 = client.post("/api/records/receive",
            headers=auth_header,
            json={
                "record_id": "record_003",
                "receive_qty": 40,
                "receive_time": None
            }
        )
        assert response2.status_code == 200, f"Second receive failed: {response2.json()}"
        
        # Verify total accumulated
        data = response2.json()
        assert data["record"]["total_receive_qty"] == 70  # 30 + 40
        assert data["record"]["partial_receive"] == 1  # Partial receive flag

    def test_return_goods(self, client, test_db, auth_header, test_factory, test_order, test_processes):
        """
        Test return goods flow:
        1. Create from_record with shipped qty and to_record with received qty
        2. Perform return
        3. Assert return record is created and quantities are reduced
        """
        from app.models.record import ProcessRecord, ReturnRecord

        # Create sender record (already shipped)
        from_record = ProcessRecord(
            record_id="record_from",
            order_id="order_001",
            process_id="proc_001",
            factory_id="factory_001",
            record_status="shipped",
            lock_type="none",
            total_receive_qty=100,
            total_ship_qty=80,  # Has shipped 80
        )
        test_db.add(from_record)

        # Create receiver record (received some)
        to_record = ProcessRecord(
            record_id="record_to",
            order_id="order_001",
            process_id="proc_002",
            factory_id="factory_001",
            record_status="received",
            lock_type="entry_lock",
            total_receive_qty=50,
            total_ship_qty=0,
        )
        test_db.add(to_record)
        test_db.commit()

        # Perform return
        response = client.post("/api/records/return",
            headers=auth_header,
            json={
                "from_record_id": "record_from",
                "to_record_id": "record_to",
                "return_qty": 10,
                "return_reason": "质量不良"
            }
        )

        assert response.status_code == 200, f"Return failed: {response.json()}"
        data = response.json()
        assert data["success"] is True
        assert "return_record" in data
        assert data["return_record"]["return_qty"] == 10
        assert data["return_record"]["return_reason"] == "质量不良"

        # Verify quantities reduced
        assert data["from_record"]["total_ship_qty"] == 70  # 80 - 10
        assert data["to_record"]["total_receive_qty"] == 40  # 50 - 10

    def test_cannot_receive_without_prev_ship(self, client, test_db, auth_header, test_factory, test_order, test_processes):
        """
        Test that receiving fails when previous process has no shipped quantity:
        1. Create a record where prev_record has total_ship_qty = 0
        2. Try to receive
        3. Assert 400 error
        """
        from app.models.record import ProcessRecord
        from app.models.process import Process

        # Create a second process (proc_002) that depends on proc_001
        # Ensure proc_001 has 0 shipped quantity

        # Create process record for proc_001 with 0 shipped
        record_proc1 = ProcessRecord(
            record_id="record_proc1",
            order_id="order_001",
            process_id="proc_001",
            factory_id="factory_001",
            record_status="pending",
            lock_type="none",
            total_receive_qty=0,
            total_ship_qty=0,  # Nothing shipped yet
        )
        test_db.add(record_proc1)

        # Create process record for proc_002 (which depends on proc_001)
        record_proc2 = ProcessRecord(
            record_id="record_proc2",
            order_id="order_001",
            process_id="proc_002",
            factory_id="factory_001",
            record_status="pending",
            lock_type="none",
            total_receive_qty=0,
            total_ship_qty=0,
        )
        test_db.add(record_proc2)
        test_db.commit()

        # Try to receive on proc_002 (which should fail because proc_001 has no shipped qty)
        response = client.post("/api/records/receive",
            headers=auth_header,
            json={
                "record_id": "record_proc2",
                "receive_qty": 10,
                "receive_time": None
            }
        )

        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "上道" in response.json().get("detail", "") or "发出量" in response.json().get("detail", "")
