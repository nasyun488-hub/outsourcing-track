#!/usr/bin/env python3
"""清空并生成电子行业铝合金结构件 100 条多工序测试订单。

数据特征：
- 100 条订单，产品均为电子行业铝合金结构件。
- 每单 4~7 道工序。
- 覆盖相邻工序同厂家、间隔工序同厂家、多厂家协作路线。
- 覆盖 pending / in_progress / completed / overdue / partial / return 等多种进度。
- 不在脚本中保存数据库密码；通过 MySQL 容器环境变量读取。
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "acceptance" / "electronics-aluminum-test-data-result.json"
MYSQL_CONTAINER = "outsourcing-track-mysql-1"


def mysql(sql: str) -> str:
    cmd = [
        "docker", "exec", "-i", MYSQL_CONTAINER, "sh", "-lc",
        'mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" outsourcing_track --batch --raw',
    ]
    p = subprocess.run(cmd, cwd=ROOT, input=sql, text=True, encoding="utf-8", capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"mysql failed\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}")
    return p.stdout.strip()


def q(v: object) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def ensure_columns(table: str, column_ddls: list[tuple[str, str]]) -> None:
    names = "','".join(name for name, _ in column_ddls)
    existing = set(mysql(f"""
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = '{table}'
  AND COLUMN_NAME IN ('{names}');
""").splitlines()[1:])
    for name, ddl in column_ddls:
        if name not in existing:
            mysql(f"SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;\nALTER TABLE {table} {ddl};")


def ensure_schema() -> None:
    ensure_columns("orders", [
        ("product_name", "ADD COLUMN product_name VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '制件名称' AFTER order_status"),
        ("product_code", "ADD COLUMN product_code VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '制件编码' AFTER product_name"),
        ("spec", "ADD COLUMN spec VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '规格型号' AFTER product_code"),
        ("unit", "ADD COLUMN unit VARCHAR(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '计量单位' AFTER spec"),
        ("delivery_date", "ADD COLUMN delivery_date DATETIME NULL COMMENT '交付日期' AFTER unit"),
        ("part_no", "ADD COLUMN part_no VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '零件号' AFTER delivery_date"),
    ])
    ensure_columns("notifications", [
        ("related_type", "ADD COLUMN related_type VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '关联业务类型' AFTER related_id"),
        ("jump_url", "ADD COLUMN jump_url VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '前端跳转URL' AFTER related_type"),
    ])


FACTORIES = [
    ("F001", "电子结构件总装主厂", "primary", "13800138000", "深圳·总装终检中心"),
    ("F002", "CNC精密加工A厂", "primary", "13800138002", "东莞·高速CNC车间"),
    ("F003", "阳极氧化B厂", "cooperative", "13800138004", "惠州·阳极氧化线"),
    ("F004", "喷砂拉丝C厂", "cooperative", "13800138007", "佛山·表面预处理线"),
    ("F005", "精密清洗D厂", "cooperative", "13800138008", "中山·超声清洗线"),
    ("F006", "激光打标E厂", "cooperative", "13800138009", "广州·镭雕追溯线"),
    ("F007", "尺寸检测F厂", "cooperative", "13800138010", "珠海·三坐标检测室"),
    ("F008", "时效整形G厂", "cooperative", "13800138011", "江门·时效整形线"),
]

USERS = [
    ("U001", "F001", "13800138000", "企业管理员", "enterprise_admin"),
    ("U002", "F001", "13800138001", "主厂管理员", "primary_admin"),
    ("U003", "F002", "13800138002", "CNC操作员", "primary_operator"),
    ("U004", "F002", "13800138003", "CNC发运员", "primary_operator"),
    ("U005", "F003", "13800138004", "阳极氧化操作员", "cooperative_operator"),
    ("U006", "F003", "13800138005", "阳极氧化管理员", "cooperative_admin"),
    ("U007", "F001", "13800138006", "终检操作员", "primary_operator"),
    ("U008", "F004", "13800138007", "喷砂操作员", "cooperative_operator"),
    ("U009", "F005", "13800138008", "清洗操作员", "cooperative_operator"),
    ("U010", "F006", "13800138009", "打标操作员", "cooperative_operator"),
    ("U011", "F007", "13800138010", "检测操作员", "cooperative_operator"),
    ("U012", "F008", "13800138011", "时效整形操作员", "cooperative_operator"),
]

FACTORY_USER = {
    "F001": "U007", "F002": "U004", "F003": "U005", "F004": "U008",
    "F005": "U009", "F006": "U010", "F007": "U011", "F008": "U012",
}

PRODUCTS = [
    "5G基站铝合金散热壳", "服务器电源铝合金散热底座", "工业相机铝合金前盖", "新能源汽车BMS铝合金支架",
    "笔记本转轴铝合金支座", "消费电子铝合金中框", "连接器铝合金屏蔽罩", "路由器铝合金散热片",
    "无人机云台铝合金支架", "平板电脑铝合金后盖", "光模块铝合金外壳", "储能控制器铝合金面板",
    "车载雷达铝合金安装座", "智能穿戴铝合金边框", "交换机铝合金导热板", "充电桩控制盒铝合金壳体",
]

ROUTES = [
    # 连续同厂家：CNC粗精加工均 F002
    [("010", "铝型材下料", "F002"), ("020", "CNC粗加工", "F002"), ("030", "CNC精加工", "F002"), ("040", "喷砂拉丝", "F004"), ("050", "阳极氧化", "F003"), ("060", "终检包装", "F001")],
    # 间隔同厂家：F003 阳极前处理和封孔复检
    [("010", "压铸去毛刺", "F002"), ("020", "时效整形", "F008"), ("030", "阳极前处理", "F003"), ("040", "激光打标", "F006"), ("050", "阳极封孔复检", "F003"), ("060", "尺寸终检", "F007"), ("070", "总装入库", "F001")],
    # 连续同厂家：喷砂+拉丝同 F004
    [("010", "CNC开粗", "F002"), ("020", "去披锋", "F005"), ("030", "喷砂", "F004"), ("040", "拉丝", "F004"), ("050", "本色阳极", "F003"), ("060", "终检包装", "F001")],
    # 间隔同厂家：F005 清洗两次
    [("010", "CNC精雕", "F002"), ("020", "超声波清洗", "F005"), ("030", "阳极氧化", "F003"), ("040", "激光二维码", "F006"), ("050", "洁净复洗", "F005"), ("060", "外观全检", "F007"), ("070", "主厂入库", "F001")],
    # 多厂普通路线
    [("010", "CNC加工", "F002"), ("020", "时效去应力", "F008"), ("030", "喷砂", "F004"), ("040", "阳极氧化", "F003"), ("050", "尺寸检测", "F007"), ("060", "终检包装", "F001")],
    # 四道短流程，连续同厂家 F001 终检+包装
    [("010", "CNC钻攻", "F002"), ("020", "清洗烘干", "F005"), ("030", "主厂终检", "F001"), ("040", "主厂包装", "F001")],
]

SPECIAL_IDS = {
    1: "MADM_FLOW_001",
    2: "DEMO_PENDING_001",
    3: "DEMO_RECEIVED_001",
    4: "DEMO_SPLIT_001",
    5: "DEMO_OVERDUE_001",
    6: "DEMO_RETURN_001",
    7: "DEMO_DONE_001",
}


def status_plan(i: int, process_count: int) -> tuple[str, list[dict], str]:
    """返回订单状态、每道工序数量状态、场景标签。"""
    qty_marker = i % 10
    if qty_marker == 0:
        return "pending", [dict(status="pending", recv=0, ship=0, lock="none", age=2) for _ in range(process_count)], "全新待接收"
    if qty_marker == 1:
        states = [dict(status="received", recv=1, ship=0, lock="entry_lock", age=8)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=2) for _ in range(process_count - 1)]
        return "in_progress", states, "首道已接收待发出"
    if qty_marker == 2:
        states = [dict(status="shipped", recv=1, ship=1, lock="relation_lock", age=5), dict(status="pending", recv=0, ship=0, lock="none", age=2)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 2)]
        return "in_progress", states[:process_count], "首道已发出下道待接收"
    if qty_marker == 3:
        states = [dict(status="completed", recv=1, ship=1, lock="sync_lock", age=36), dict(status="received", recv=1, ship=0, lock="entry_lock", age=4)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 2)]
        return "in_progress", states[:process_count], "中道已接收待发出"
    if qty_marker == 4:
        states = [dict(status="shipped", recv=1, ship=0.6, lock="relation_lock", age=10), dict(status="received", recv=0.6, ship=0, lock="entry_lock", age=3)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 2)]
        return "in_progress", states[:process_count], "分批流转部分到达"
    if qty_marker == 5:
        return "completed", [dict(status="completed", recv=1, ship=1, lock="sync_lock", age=80 - n * 6) for n in range(process_count)], "全流程已完成"
    if qty_marker == 6:
        states = [dict(status="received", recv=1, ship=0, lock="entry_lock", age=72)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=72) for _ in range(process_count - 1)]
        return "in_progress", states, "超期未发出"
    if qty_marker == 7:
        states = [dict(status="completed", recv=1, ship=1, lock="sync_lock", age=40), dict(status="shipped", recv=1, ship=0.75, lock="relation_lock", age=20), dict(status="pending", recv=0, ship=0, lock="none", age=2)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 3)]
        return "in_progress", states[:process_count], "二道部分发出"
    if qty_marker == 8:
        states = [dict(status="shipped", recv=1, ship=0.85, lock="entry_lock", age=24), dict(status="received", recv=0.75, ship=0, lock="entry_lock", age=18)]
        states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 2)]
        return "in_progress", states[:process_count], "退件补发中"
    states = [dict(status="completed", recv=1, ship=1, lock="sync_lock", age=70), dict(status="completed", recv=1, ship=1, lock="sync_lock", age=60), dict(status="received", recv=1, ship=0, lock="entry_lock", age=30)]
    states += [dict(status="pending", recv=0, ship=0, lock="none", age=1) for _ in range(process_count - 3)]
    return "in_progress", states[:process_count], "后段待发出"


def build_sql() -> tuple[str, dict]:
    orders, processes, records = [], [], []
    receive_batches, ship_batches, returns = [], [], []
    notifications, logs = [], []
    scenario_counts: dict[str, int] = {}
    contiguous_repeat = 0
    interval_repeat = 0

    for i in range(1, 101):
        order_id = SPECIAL_IDS.get(i, f"ELEC_AL_{i:03d}")
        route = ROUTES[(i - 1) % len(ROUTES)]
        process_count = len(route)
        qty = 40 + (i % 9) * 10
        order_status, states, scenario = status_plan(i, process_count)
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        product = PRODUCTS[(i - 1) % len(PRODUCTS)]
        code = f"EA-AL-{i:03d}"
        spec = f"铝合金6061-T6 {80 + i % 7 * 10}×{45 + i % 5 * 8}×{6 + i % 4}mm"
        part_no = f"AL-ELEC-{20260600 + i}"
        delivery_expr = f"DATE_ADD(NOW(), INTERVAL {3 + i % 18} DAY)" if order_status != "completed" else f"DATE_SUB(NOW(), INTERVAL {1 + i % 5} DAY)"
        created_expr = f"DATE_SUB(NOW(), INTERVAL {1 + i % 12} DAY)"
        updated_expr = "NOW()"
        orders.append(f"({q(order_id)}, 'F001', {q(order_status)}, {q(product)}, {q(code)}, {q(spec)}, '件', {delivery_expr}, {q(part_no)}, {qty}, {created_expr}, {created_expr}, {updated_expr})")

        factories_in_route = [f for _, _, f in route]
        if any(factories_in_route[n] == factories_in_route[n - 1] for n in range(1, len(factories_in_route))):
            contiguous_repeat += 1
        seen: dict[str, list[int]] = {}
        for pos, fid in enumerate(factories_in_route):
            seen.setdefault(fid, []).append(pos)
        if any(any(b - a > 1 for a, b in zip(pos, pos[1:])) for pos in seen.values()):
            interval_repeat += 1

        for idx, (seq, name, factory_id) in enumerate(route, start=1):
            process_id = f"{order_id}_P{idx:02d}"
            record_id = f"{order_id}_R{idx:02d}"
            state = states[idx - 1]
            recv = int(qty * state["recv"])
            ship = int(qty * state["ship"])
            age = int(state["age"])
            last_recv = "NULL" if recv == 0 else f"DATE_SUB(NOW(), INTERVAL {age} HOUR)"
            last_ship = "NULL" if ship == 0 else f"DATE_SUB(NOW(), INTERVAL {max(age - 2, 1)} HOUR)"
            created = f"DATE_SUB(NOW(), INTERVAL {max(age, 1)} HOUR)"
            partial_recv = 1 if recv and recv < qty else 0
            partial_ship = 1 if ship and ship < recv else 0
            processes.append(f"({q(process_id)}, {q(order_id)}, {q(seq)}, {q(name)}, {q(factory_id)}, {idx}, {created}, NOW())")
            records.append(f"({q(record_id)}, {q(order_id)}, {q(process_id)}, {q(factory_id)}, {q(state['status'])}, {q(state['lock'])}, {recv}, {ship}, {partial_recv}, {partial_ship}, {last_recv}, {last_ship}, {created}, NOW())")
            user_id = FACTORY_USER[factory_id]
            if recv > 0:
                if partial_recv:
                    r1 = max(recv // 2, 1)
                    r2 = recv - r1
                    receive_batches.append(f"({q(record_id + '_RB01')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {age} HOUR), {r1}, 1, 0, NOW(), NOW())")
                    if r2 > 0:
                        receive_batches.append(f"({q(record_id + '_RB02')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {max(age - 1, 1)} HOUR), {r2}, 2, 0, NOW(), NOW())")
                else:
                    receive_batches.append(f"({q(record_id + '_RB01')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {age} HOUR), {recv}, 1, 0, NOW(), NOW())")
            if ship > 0:
                if partial_ship:
                    s1 = max(ship // 2, 1)
                    s2 = ship - s1
                    ship_batches.append(f"({q(record_id + '_SB01')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {max(age - 2, 1)} HOUR), {s1}, 1, NOW(), NOW())")
                    if s2 > 0:
                        ship_batches.append(f"({q(record_id + '_SB02')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {max(age - 1, 1)} HOUR), {s2}, 2, NOW(), NOW())")
                else:
                    ship_batches.append(f"({q(record_id + '_SB01')}, {q(record_id)}, {q(user_id)}, DATE_SUB(NOW(), INTERVAL {max(age - 2, 1)} HOUR), {ship}, 1, NOW(), NOW())")

        if i % 10 == 8 and process_count >= 2:
            rid1 = f"{order_id}_R01"
            rid2 = f"{order_id}_R02"
            ret_qty = max(qty // 10, 5)
            returns.append(f"({q(order_id + '_RET01')}, {q(rid1)}, {q(rid2)}, {q(FACTORY_USER[route[1][2]])}, '阳极色差/尺寸复检不合格，退回上道补加工', {ret_qty}, DATE_SUB(NOW(), INTERVAL 4 HOUR))")

        if i <= 20 or i % 10 in {1, 6, 8}:
            notifications.append(f"({q(order_id + '_N01')}, 'U001', {q('订单进度提醒')}, {q(order_id + '：' + scenario + '，产品为' + product)}, 'transfer', 0, {q(order_id)}, 'order', {q('/kanban/' + order_id)}, NOW())")
        logs.append(f"({q(order_id + '_LOG01')}, 'U001', 'GEN_ELEC_AL_CASE', 'orders', {q(order_id)}, NULL, JSON_OBJECT('scenario', {q(scenario)}, 'process_count', {process_count}), '127.0.0.1', NOW())")

    prelude = """
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM action_logs;
DELETE FROM approval_requests;
DELETE FROM notifications;
DELETE FROM return_records;
DELETE FROM receive_batches;
DELETE FROM ship_batches;
DELETE FROM process_records;
DELETE FROM processes;
DELETE FROM orders;
DELETE FROM sms_codes WHERE phone LIKE '13800138%';
DELETE FROM users WHERE phone LIKE '13800138%' OR user_id LIKE 'U___' OR user_id LIKE 'DEMO_%';
DELETE FROM factories WHERE factory_id LIKE 'F___' OR factory_id LIKE 'DEMO_%';
SET FOREIGN_KEY_CHECKS=1;
"""
    factory_sql = "INSERT INTO factories(factory_id, factory_name, factory_type, factory_phone, factory_address, status, created_at, updated_at) VALUES\n" + ",\n".join(
        f"({q(fid)}, {q(name)}, {q(ftype)}, {q(phone)}, {q(addr)}, 'active', NOW(), NOW())" for fid, name, ftype, phone, addr in FACTORIES
    ) + ";\n"
    user_sql = "INSERT INTO users(user_id, factory_id, phone, name, role, password_hash, status, created_at, updated_at) VALUES\n" + ",\n".join(
        f"({q(uid)}, {q(fid)}, {q(phone)}, {q(name)}, {q(role)}, 'demo_hash', 'active', NOW(), NOW())" for uid, fid, phone, name, role in USERS
    ) + ";\n"
    sql = prelude + factory_sql + user_sql
    sql += "INSERT INTO orders(order_id, primary_factory_id, order_status, product_name, product_code, spec, unit, delivery_date, part_no, total_qty, mom_created_at, created_at, updated_at) VALUES\n" + ",\n".join(orders) + ";\n"
    sql += "INSERT INTO processes(process_id, order_id, process_seq, process_name, factory_id, process_order, created_at, updated_at) VALUES\n" + ",\n".join(processes) + ";\n"
    sql += "INSERT INTO process_records(record_id, order_id, process_id, factory_id, record_status, lock_type, total_receive_qty, total_ship_qty, partial_receive, partial_ship, last_receive_time, last_ship_time, created_at, updated_at) VALUES\n" + ",\n".join(records) + ";\n"
    if receive_batches:
        sql += "INSERT INTO receive_batches(batch_id, record_id, user_id, receive_time, receive_qty, batch_no, return_qty, created_at, updated_at) VALUES\n" + ",\n".join(receive_batches) + ";\n"
    if ship_batches:
        sql += "INSERT INTO ship_batches(batch_id, record_id, user_id, ship_time, ship_qty, batch_no, created_at, updated_at) VALUES\n" + ",\n".join(ship_batches) + ";\n"
    if returns:
        sql += "INSERT INTO return_records(return_id, from_record_id, to_record_id, user_id, return_reason, return_qty, created_at) VALUES\n" + ",\n".join(returns) + ";\n"
    if notifications:
        sql += "INSERT INTO notifications(notif_id, user_id, title, content, notif_type, is_read, related_id, related_type, jump_url, created_at) VALUES\n" + ",\n".join(notifications) + ";\n"
    if logs:
        sql += "INSERT INTO action_logs(log_id, user_id, action_type, target_table, target_id, old_value, new_value, ip_address, created_at) VALUES\n" + ",\n".join(logs) + ";\n"

    meta = {
        "orders": 100,
        "factories": len(FACTORIES),
        "users": len(USERS),
        "processes": len(processes),
        "records": len(records),
        "receive_batches": len(receive_batches),
        "ship_batches": len(ship_batches),
        "return_records": len(returns),
        "notifications": len(notifications),
        "contiguous_repeat_orders": contiguous_repeat,
        "interval_repeat_orders": interval_repeat,
        "scenario_counts": scenario_counts,
        "sample_login_phones": {
            "enterprise_admin": "13800138000",
            "cnc_operator": "13800138003",
            "anodizing_operator": "13800138004",
            "surface_operator": "13800138007",
            "final_operator": "13800138006",
        },
        "compatible_sample_qr": {
            "pending_receive": "record_DEMO_PENDING_001_R01",
            "ship_ready": "record_DEMO_RECEIVED_001_R01",
            "split_view": "record_DEMO_SPLIT_001_R01",
            "overdue_ship": "record_DEMO_OVERDUE_001_R01",
            "done_view": "record_DEMO_DONE_001_R01",
        },
    }
    return sql, meta


VERIFY_SQL = """
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT 'orders' item, COUNT(*) count FROM orders;
SELECT 'processes' item, COUNT(*) count FROM processes;
SELECT 'records' item, COUNT(*) count FROM process_records;
SELECT 'contiguous_same_factory_orders' item, COUNT(DISTINCT p1.order_id) count
FROM processes p1 JOIN processes p2 ON p2.order_id=p1.order_id AND p2.process_order=p1.process_order+1 AND p2.factory_id=p1.factory_id;
SELECT 'interval_same_factory_orders' item, COUNT(DISTINCT p1.order_id) count
FROM processes p1 JOIN processes p2 ON p2.order_id=p1.order_id AND p2.factory_id=p1.factory_id AND p2.process_order>p1.process_order+1;
SELECT order_status, COUNT(*) count FROM orders GROUP BY order_status ORDER BY order_status;
SELECT record_status, COUNT(*) count FROM process_records GROUP BY record_status ORDER BY record_status;
SELECT 'bad_process_count' check_name, COUNT(*) bad_count
FROM (SELECT order_id, COUNT(*) c FROM processes GROUP BY order_id) x WHERE c < 4;
SELECT 'qty_invalid' check_name, COUNT(*) bad_count
FROM process_records WHERE total_receive_qty < 0 OR total_ship_qty < 0 OR total_ship_qty > total_receive_qty;
SELECT 'downstream_receive_exceeds_prev_ship' check_name, COUNT(*) bad_count
FROM process_records curr
JOIN processes cp ON cp.process_id=curr.process_id
JOIN processes pp ON pp.order_id=cp.order_id AND pp.process_order=cp.process_order-1
JOIN process_records prev ON prev.process_id=pp.process_id
WHERE curr.total_receive_qty > prev.total_ship_qty;
SELECT order_id, product_name, order_status, total_qty FROM orders ORDER BY order_id LIMIT 12;
"""


def main() -> None:
    ensure_schema()
    sql, meta = build_sql()
    mysql(sql)
    verification = mysql(VERIFY_SQL)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok",
        "dataset": "电子行业铝合金结构件多工序订单测试集",
        "meta": meta,
        "verification_raw": verification,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
