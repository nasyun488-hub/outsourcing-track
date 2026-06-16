#!/usr/bin/env python3
"""扩展外协系统演示数据到 40+ 订单样本。

运行前建议先执行 scripts/generate_demo_data.py 重置基础样本；本脚本只清理/重建 BULK_* 扩展样本。
不在脚本中保存数据库密码，通过 mysql 容器内 MYSQL_ROOT_PASSWORD 读取。
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "acceptance" / "demo-data-40-plus-result.json"
MYSQL_CONTAINER = "outsourcing-track-mysql-1"
SAMPLE_COUNT = 42

PRODUCTS = [
    ("减速箱端盖", "PRD-BK", "HT250 Φ220", "PART-BK"),
    ("液压阀芯", "PRD-VS", "40Cr Φ32×180", "PART-VS"),
    ("机器人关节座", "PRD-RJ", "7075-T6 160×110", "PART-RJ"),
    ("导向套", "PRD-GS", "GCr15 HRC58", "PART-GS"),
    ("联轴器半体", "PRD-CP", "45钢 Φ95", "PART-CP"),
    ("泵体毛坯", "PRD-PB", "铸铝 A356", "PART-PB"),
    ("定位销轴", "PRD-PN", "20CrMnTi Φ18", "PART-PN"),
    ("法兰盘", "PRD-FL", "Q235 Φ260", "PART-FL"),
]

SCENARIOS = ["pending", "first_received", "first_shipped", "second_received", "second_shipped", "completed", "overdue", "return"]


def mysql(sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", MYSQL_CONTAINER, "sh", "-lc",
        'mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" outsourcing_track --batch --raw',
    ]
    p = subprocess.run(cmd, cwd=ROOT, input=sql, text=True, encoding="utf-8", capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"mysql failed\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}")
    return p.stdout.strip()


def q(s: str) -> str:
    return s.replace("'", "''")


def build_sql() -> str:
    order_values: list[str] = []
    process_values: list[str] = []
    record_values: list[str] = []
    receive_values: list[str] = []
    ship_values: list[str] = []
    return_values: list[str] = []
    notif_values: list[str] = []

    for i in range(1, SAMPLE_COUNT + 1):
        oid = f"BULK_ORDER_{i:03d}"
        product_name, product_code_prefix, spec, part_prefix = PRODUCTS[(i - 1) % len(PRODUCTS)]
        scenario = SCENARIOS[(i - 1) % len(SCENARIOS)]
        qty = 30 + (i % 9) * 10
        second_factory = "F004" if i % 10 == 0 else "F003"
        second_user = "U008" if second_factory == "F004" else "U005"
        status = {
            "pending": "pending",
            "completed": "completed",
        }.get(scenario, "in_progress")
        created_expr = "DATE_SUB(NOW(), INTERVAL 60 HOUR)" if scenario == "overdue" else f"DATE_SUB(NOW(), INTERVAL {i % 24} HOUR)"
        delivery_expr = f"DATE_ADD(NOW(), INTERVAL {3 + (i % 20)} DAY)"
        order_values.append(
            f"('{oid}','F002','{status}','{q(product_name)}','{product_code_prefix}-{i:03d}','{q(spec)}','件',{delivery_expr},'{part_prefix}-{i:03d}',{qty},{created_expr},{created_expr},NOW())"
        )
        p1, p2, p3 = f"BULK_P_{i:03d}_1", f"BULK_P_{i:03d}_2", f"BULK_P_{i:03d}_3"
        r1, r2, r3 = f"BULK_R_{i:03d}_1", f"BULK_R_{i:03d}_2", f"BULK_R_{i:03d}_3"
        p2_name = "二道表面处理" if second_factory == "F004" else "二道热处理"
        process_values.extend([
            f"('{p1}','{oid}','010','首道精加工','F002',1,{created_expr},NOW())",
            f"('{p2}','{oid}','020','{p2_name}','{second_factory}',2,{created_expr},NOW())",
            f"('{p3}','{oid}','030','末道总装终检','F001',3,{created_expr},NOW())",
        ])

        # default quantities
        r1_recv = r1_ship = r2_recv = r2_ship = r3_recv = r3_ship = 0
        r1_status = r2_status = r3_status = "pending"
        r1_lock = r2_lock = r3_lock = "none"
        r1_recv_time = r1_ship_time = r2_recv_time = r2_ship_time = r3_recv_time = r3_ship_time = "NULL"
        r1_pr = r1_ps = r2_pr = r2_ps = r3_pr = r3_ps = 0

        if scenario == "first_received":
            r1_recv = qty // 2; r1_status = "received"; r1_lock = "entry_lock"; r1_recv_time = "DATE_SUB(NOW(), INTERVAL 3 HOUR)"
        elif scenario == "first_shipped":
            r1_recv = qty; r1_ship = qty // 2; r1_status = "shipped"; r1_lock = "entry_lock"; r1_recv_time = "DATE_SUB(NOW(), INTERVAL 6 HOUR)"; r1_ship_time = "DATE_SUB(NOW(), INTERVAL 2 HOUR)"; r1_ps = 1
        elif scenario == "second_received":
            r1_recv = qty; r1_ship = qty; r2_recv = qty // 2
            r1_status = "shipped"; r1_lock = "relation_lock"; r2_status = "received"; r2_lock = "entry_lock"
            r1_recv_time = "DATE_SUB(NOW(), INTERVAL 8 HOUR)"; r1_ship_time = "DATE_SUB(NOW(), INTERVAL 5 HOUR)"; r2_recv_time = "DATE_SUB(NOW(), INTERVAL 3 HOUR)"
            r2_pr = 1
        elif scenario == "second_shipped":
            r1_recv = r1_ship = r2_recv = qty; r2_ship = qty // 2
            r1_status = "shipped"; r1_lock = "relation_lock"; r2_status = "shipped"; r2_lock = "entry_lock"
            r1_recv_time = "DATE_SUB(NOW(), INTERVAL 10 HOUR)"; r1_ship_time = "DATE_SUB(NOW(), INTERVAL 8 HOUR)"; r2_recv_time = "DATE_SUB(NOW(), INTERVAL 6 HOUR)"; r2_ship_time = "DATE_SUB(NOW(), INTERVAL 2 HOUR)"; r2_ps = 1
        elif scenario == "completed":
            r1_recv = r1_ship = r2_recv = r2_ship = r3_recv = r3_ship = qty
            r1_status = r2_status = r3_status = "completed"; r1_lock = r2_lock = r3_lock = "sync_lock"
            r1_recv_time = "DATE_SUB(NOW(), INTERVAL 3 DAY)"; r1_ship_time = "DATE_SUB(NOW(), INTERVAL 2 DAY)"; r2_recv_time = "DATE_SUB(NOW(), INTERVAL 40 HOUR)"; r2_ship_time = "DATE_SUB(NOW(), INTERVAL 28 HOUR)"; r3_recv_time = "DATE_SUB(NOW(), INTERVAL 20 HOUR)"; r3_ship_time = "DATE_SUB(NOW(), INTERVAL 12 HOUR)"
        elif scenario == "overdue":
            r1_recv = qty; r1_status = "received"; r1_lock = "entry_lock"; r1_recv_time = "DATE_SUB(NOW(), INTERVAL 55 HOUR)"
        elif scenario == "return":
            r1_recv = qty; r1_ship = qty; r2_recv = qty; returned = max(1, qty // 10)
            r1_status = "shipped"; r1_lock = "entry_lock"; r2_status = "received"; r2_lock = "entry_lock"
            r1_recv_time = "DATE_SUB(NOW(), INTERVAL 18 HOUR)"; r1_ship_time = "DATE_SUB(NOW(), INTERVAL 14 HOUR)"; r2_recv_time = "DATE_SUB(NOW(), INTERVAL 10 HOUR)"; r1_ps = r2_pr = 1
            return_values.append(f"('BULK_RET_{i:03d}','{r1}','{r2}','{second_user}','抽检不合格退回补加工',{returned},DATE_SUB(NOW(), INTERVAL 5 HOUR))")

        record_values.extend([
            f"('{r1}','{oid}','{p1}','F002','{r1_status}','{r1_lock}',{r1_recv},{r1_ship},{r1_pr},{r1_ps},{r1_recv_time},{r1_ship_time},{created_expr},NOW())",
            f"('{r2}','{oid}','{p2}','{second_factory}','{r2_status}','{r2_lock}',{r2_recv},{r2_ship},{r2_pr},{r2_ps},{r2_recv_time},{r2_ship_time},{created_expr},NOW())",
            f"('{r3}','{oid}','{p3}','F001','{r3_status}','{r3_lock}',{r3_recv},{r3_ship},{r3_pr},{r3_ps},{r3_recv_time},{r3_ship_time},{created_expr},NOW())",
        ])

        if r1_recv:
            receive_values.append(f"('BULK_RB_{i:03d}_1','{r1}','U004',{r1_recv_time},{r1_recv},1,0,NOW(),NOW())")
        if r1_ship:
            ship_values.append(f"('BULK_SB_{i:03d}_1','{r1}','U004',{r1_ship_time},{r1_ship},1,NOW(),NOW())")
        if r2_recv:
            receive_values.append(f"('BULK_RB_{i:03d}_2','{r2}','{second_user}',{r2_recv_time},{r2_recv},1,{max(1, qty // 10) if scenario == 'return' else 0},NOW(),NOW())")
        if r2_ship:
            ship_values.append(f"('BULK_SB_{i:03d}_2','{r2}','{second_user}',{r2_ship_time},{r2_ship},1,NOW(),NOW())")
        if r3_recv:
            receive_values.append(f"('BULK_RB_{i:03d}_3','{r3}','U007',{r3_recv_time},{r3_recv},1,0,NOW(),NOW())")
        if r3_ship:
            ship_values.append(f"('BULK_SB_{i:03d}_3','{r3}','U007',{r3_ship_time},{r3_ship},1,NOW(),NOW())")

        target_user = {"F003": "U005", "F004": "U008"}[second_factory]
        if scenario in ("second_received", "return"):
            notif_values.append(f"('BULK_N_{i:03d}_2','{target_user}','待处理工序提醒','订单 {oid} 已进入本道处理，请及时发出。','transfer',0,'{oid}','order','/kanban/{oid}',DATE_SUB(NOW(), INTERVAL 30 MINUTE))")
        if scenario == "overdue":
            notif_values.append(f"('BULK_N_{i:03d}_1','U004','超期发出提醒','订单 {oid} 首道已接收超过48小时未发出。','transfer',0,'{oid}','order','/kanban/{oid}',DATE_SUB(NOW(), INTERVAL 20 MINUTE))")

    sql_parts = [
        "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "SET FOREIGN_KEY_CHECKS=0;",
        "DELETE FROM action_logs WHERE target_id LIKE 'BULK_%' OR log_id LIKE 'BULK_%';",
        "DELETE FROM notifications WHERE notif_id LIKE 'BULK_%' OR related_id LIKE 'BULK_%';",
        "DELETE FROM return_records WHERE return_id LIKE 'BULK_%' OR from_record_id LIKE 'BULK_%' OR to_record_id LIKE 'BULK_%';",
        "DELETE FROM receive_batches WHERE batch_id LIKE 'BULK_%' OR record_id LIKE 'BULK_%';",
        "DELETE FROM ship_batches WHERE batch_id LIKE 'BULK_%' OR record_id LIKE 'BULK_%';",
        "DELETE FROM process_records WHERE record_id LIKE 'BULK_%' OR order_id LIKE 'BULK_%';",
        "DELETE FROM processes WHERE process_id LIKE 'BULK_%' OR order_id LIKE 'BULK_%';",
        "DELETE FROM orders WHERE order_id LIKE 'BULK_%';",
        "SET FOREIGN_KEY_CHECKS=1;",
        "INSERT INTO orders(order_id, primary_factory_id, order_status, product_name, product_code, spec, unit, delivery_date, part_no, total_qty, mom_created_at, created_at, updated_at) VALUES\n" + ",\n".join(order_values) + ";",
        "INSERT INTO processes(process_id, order_id, process_seq, process_name, factory_id, process_order, created_at, updated_at) VALUES\n" + ",\n".join(process_values) + ";",
        "INSERT INTO process_records(record_id, order_id, process_id, factory_id, record_status, lock_type, total_receive_qty, total_ship_qty, partial_receive, partial_ship, last_receive_time, last_ship_time, created_at, updated_at) VALUES\n" + ",\n".join(record_values) + ";",
    ]
    if receive_values:
        sql_parts.append("INSERT INTO receive_batches(batch_id, record_id, user_id, receive_time, receive_qty, batch_no, return_qty, created_at, updated_at) VALUES\n" + ",\n".join(receive_values) + ";")
    if ship_values:
        sql_parts.append("INSERT INTO ship_batches(batch_id, record_id, user_id, ship_time, ship_qty, batch_no, created_at, updated_at) VALUES\n" + ",\n".join(ship_values) + ";")
    if return_values:
        sql_parts.append("INSERT INTO return_records(return_id, from_record_id, to_record_id, user_id, return_reason, return_qty, created_at) VALUES\n" + ",\n".join(return_values) + ";")
    if notif_values:
        sql_parts.append("INSERT INTO notifications(notif_id, user_id, title, content, notif_type, is_read, related_id, related_type, jump_url, created_at) VALUES\n" + ",\n".join(notif_values) + ";")
    return "\n".join(sql_parts)


VERIFY_SQL = """
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT 'orders' item, COUNT(*) count FROM orders;
SELECT 'bulk_orders' item, COUNT(*) count FROM orders WHERE order_id LIKE 'BULK_%';
SELECT 'records' item, COUNT(*) count FROM process_records;
SELECT 'factories_participating' item, COUNT(DISTINCT factory_id) count FROM process_records;
SELECT order_status, COUNT(*) count FROM orders GROUP BY order_status ORDER BY order_status;
SELECT factory_id, COUNT(*) records FROM process_records GROUP BY factory_id ORDER BY factory_id;
SELECT 'order_without_3_processes' check_name, COUNT(*) bad_count
FROM orders o LEFT JOIN (SELECT order_id, COUNT(*) c FROM processes GROUP BY order_id) p ON p.order_id=o.order_id
WHERE p.c <> 3 OR p.c IS NULL;
SELECT 'downstream_receive_exceeds_prev_ship' check_name, COUNT(*) bad_count
FROM process_records curr
JOIN processes cp ON cp.process_id=curr.process_id
JOIN processes pp ON pp.order_id=cp.order_id AND pp.process_order=cp.process_order-1
JOIN process_records prev ON prev.process_id=pp.process_id
WHERE curr.total_receive_qty > prev.total_ship_qty;
SELECT 'ship_exceeds_receive' check_name, COUNT(*) bad_count
FROM process_records WHERE total_ship_qty > total_receive_qty;
SELECT 'mojibake_notifications' check_name, COUNT(*) bad_count
FROM notifications WHERE title REGEXP 'Ã|Â|â|�|ç|æ|è|ä' OR content REGEXP 'Ã|Â|â|�|ç|æ|è|ä';
"""


def main() -> None:
    mysql(build_sql())
    verification = mysql(VERIFY_SQL)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok",
        "added_bulk_orders": SAMPLE_COUNT,
        "expected_total_orders_min": 40,
        "verification_raw": verification,
        "sample_orders": [f"BULK_ORDER_{i:03d}" for i in range(1, min(SAMPLE_COUNT, 12) + 1)],
        "role_coverage": ["enterprise_admin", "primary_admin", "a_factory_operator", "b_factory_operator", "surface_operator", "final_process_operator"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"RESULT_FILE={OUT}")


if __name__ == "__main__":
    main()
