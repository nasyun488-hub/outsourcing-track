#!/usr/bin/env python3
"""
重新生成外协流转业务模拟数据。

特点：
- 不在脚本中保存数据库密码；通过 mysql 容器内 MYSQL_ROOT_PASSWORD 读取。
- 清空业务模拟数据表（订单/工序/流转/通知/测试用户/测试厂家等），不删除数据库配置和表结构。
- MySQL 客户端强制使用 utf8mb4，避免中文被 latin1 连接写成乱码。
- 覆盖：待处理、已接收待发出、跨厂家分批流转、超期、退件补发、已完成、通知、权限测试用户。
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "acceptance" / "demo-data-result.json"


MYSQL_CONTAINER = "outsourcing-track-mysql-1"


def mysql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        MYSQL_CONTAINER,
        "sh",
        "-lc",
        'mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" outsourcing_track --batch --raw',
    ]
    p = subprocess.run(cmd, cwd=ROOT, input=sql, text=True, encoding="utf-8", capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"mysql failed\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}")
    return p.stdout.strip()


def ensure_columns(table: str, column_ddls: list[tuple[str, str]]) -> None:
    """补齐接口需要的字段，兼容旧 MySQL 版本不支持 ADD COLUMN IF NOT EXISTS。"""
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


def ensure_order_columns() -> None:
    ensure_columns("orders", [
        ("product_name", "ADD COLUMN product_name VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '制件名称' AFTER order_status"),
        ("product_code", "ADD COLUMN product_code VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '制件编码' AFTER product_name"),
        ("spec", "ADD COLUMN spec VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '规格型号' AFTER product_code"),
        ("unit", "ADD COLUMN unit VARCHAR(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '计量单位' AFTER spec"),
        ("delivery_date", "ADD COLUMN delivery_date DATETIME NULL COMMENT '交付日期' AFTER unit"),
        ("part_no", "ADD COLUMN part_no VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '零件号' AFTER delivery_date"),
    ])


def ensure_notification_columns() -> None:
    ensure_columns("notifications", [
        ("related_type", "ADD COLUMN related_type VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '关联业务类型' AFTER related_id"),
        ("jump_url", "ADD COLUMN jump_url VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '前端跳转URL' AFTER related_type"),
    ])


SQL = r"""
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS=0;

-- 清除全部模拟业务数据：本环境中业务数据均为演示/验收数据；保留数据库、表结构和外部配置。
DELETE FROM action_logs;
DELETE FROM approval_requests;
DELETE FROM notifications;
DELETE FROM return_records;
DELETE FROM receive_batches;
DELETE FROM ship_batches;
DELETE FROM process_records;
DELETE FROM processes;
DELETE FROM orders;
DELETE FROM sms_codes WHERE phone LIKE '1380013800%';
DELETE FROM users WHERE phone LIKE '1380013800%' OR user_id LIKE 'U___' OR user_id LIKE 'DEMO_%';
DELETE FROM factories WHERE factory_id LIKE 'F___' OR factory_id LIKE 'DEMO_%';

SET FOREIGN_KEY_CHECKS=1;

INSERT INTO factories(factory_id, factory_name, factory_type, factory_phone, factory_address, status, created_at, updated_at)
VALUES
('F001','总装主厂','primary','13800138000','一号厂区·总装与终检','active',NOW(),NOW()),
('F002','精加工A厂','primary','13800138002','二号厂区·车铣磨','active',NOW(),NOW()),
('F003','热处理B厂','cooperative','13800138004','三号厂区·淬火回火','active',NOW(),NOW()),
('F004','表面处理C厂','cooperative','13800138007','四号厂区·喷涂氧化','active',NOW(),NOW());

INSERT INTO users(user_id, factory_id, phone, name, role, password_hash, status, created_at, updated_at)
VALUES
('U001','F001','13800138000','企业管理员','enterprise_admin','demo_hash','active',NOW(),NOW()),
('U002','F001','13800138001','主厂管理员','primary_admin','demo_hash','active',NOW(),NOW()),
('U003','F002','13800138002','A厂操作员','primary_operator','demo_hash','active',NOW(),NOW()),
('U004','F002','13800138003','A厂发运员','primary_operator','demo_hash','active',NOW(),NOW()),
('U005','F003','13800138004','B厂操作员','cooperative_operator','demo_hash','active',NOW(),NOW()),
('U006','F003','13800138005','B厂管理员','cooperative_admin','demo_hash','active',NOW(),NOW()),
('U007','F001','13800138006','末道操作员','primary_operator','demo_hash','active',NOW(),NOW()),
('U008','F004','13800138007','C厂操作员','cooperative_operator','demo_hash','active',NOW(),NOW());

-- 订单场景：每单三道工序，路线固定为 F002 精加工 -> F003 热处理 -> F001 总装终检。
INSERT INTO orders(order_id, primary_factory_id, order_status, product_name, product_code, spec, unit, delivery_date, part_no, total_qty, mom_created_at, created_at, updated_at)
VALUES
('MADM_FLOW_001','F002','pending','航空支架组件','PRD-ZJ-001','铝合金 120×80','件',DATE_ADD(NOW(), INTERVAL 7 DAY),'PART-A001',100,NOW(),NOW(),NOW()),
('DEMO_PENDING_001','F002','pending','传动轴毛坯','PRD-ZJ-002','45钢 Φ60×320','件',DATE_ADD(NOW(), INTERVAL 10 DAY),'PART-T002',80,NOW(),NOW(),NOW()),
('DEMO_RECEIVED_001','F002','in_progress','精密阀体','PRD-ZJ-003','不锈钢 DN25','件',DATE_ADD(NOW(), INTERVAL 5 DAY),'PART-V003',50,DATE_SUB(NOW(), INTERVAL 2 HOUR),DATE_SUB(NOW(), INTERVAL 2 HOUR),NOW()),
('DEMO_SPLIT_001','F002','in_progress','泵壳半成品','PRD-ZJ-004','铸铝 A356','件',DATE_ADD(NOW(), INTERVAL 6 DAY),'PART-P004',100,DATE_SUB(NOW(), INTERVAL 6 HOUR),DATE_SUB(NOW(), INTERVAL 6 HOUR),NOW()),
('DEMO_OVERDUE_001','F002','in_progress','连接法兰','PRD-ZJ-005','Q235 Φ180','件',DATE_ADD(NOW(), INTERVAL 2 DAY),'PART-F005',60,DATE_SUB(NOW(), INTERVAL 4 DAY),DATE_SUB(NOW(), INTERVAL 4 DAY),NOW()),
('DEMO_RETURN_001','F002','in_progress','齿轮轴','PRD-ZJ-006','20CrMnTi M2.5','件',DATE_ADD(NOW(), INTERVAL 8 DAY),'PART-G006',90,DATE_SUB(NOW(), INTERVAL 1 DAY),DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),
('DEMO_DONE_001','F002','completed','导轨滑块','PRD-ZJ-007','GCr15 H级','件',DATE_SUB(NOW(), INTERVAL 1 DAY),'PART-S007',120,DATE_SUB(NOW(), INTERVAL 3 DAY),DATE_SUB(NOW(), INTERVAL 3 DAY),NOW());

INSERT INTO processes(process_id, order_id, process_seq, process_name, factory_id, process_order, created_at, updated_at)
VALUES
('MADM_P1','MADM_FLOW_001','010','首道精加工','F002',1,NOW(),NOW()),
('MADM_P2','MADM_FLOW_001','020','二道热处理','F003',2,NOW(),NOW()),
('MADM_P3','MADM_FLOW_001','030','末道总装终检','F001',3,NOW(),NOW()),

('DEMO_PENDING_P1','DEMO_PENDING_001','010','首道精加工','F002',1,NOW(),NOW()),
('DEMO_PENDING_P2','DEMO_PENDING_001','020','二道热处理','F003',2,NOW(),NOW()),
('DEMO_PENDING_P3','DEMO_PENDING_001','030','末道总装终检','F001',3,NOW(),NOW()),

('DEMO_RECEIVED_P1','DEMO_RECEIVED_001','010','首道精加工','F002',1,NOW(),NOW()),
('DEMO_RECEIVED_P2','DEMO_RECEIVED_001','020','二道热处理','F003',2,NOW(),NOW()),
('DEMO_RECEIVED_P3','DEMO_RECEIVED_001','030','末道总装终检','F001',3,NOW(),NOW()),

('DEMO_SPLIT_P1','DEMO_SPLIT_001','010','首道精加工','F002',1,NOW(),NOW()),
('DEMO_SPLIT_P2','DEMO_SPLIT_001','020','二道热处理','F003',2,NOW(),NOW()),
('DEMO_SPLIT_P3','DEMO_SPLIT_001','030','末道总装终检','F001',3,NOW(),NOW()),

('DEMO_OVERDUE_P1','DEMO_OVERDUE_001','010','首道精加工','F002',1,DATE_SUB(NOW(), INTERVAL 4 DAY),NOW()),
('DEMO_OVERDUE_P2','DEMO_OVERDUE_001','020','二道热处理','F003',2,DATE_SUB(NOW(), INTERVAL 4 DAY),NOW()),
('DEMO_OVERDUE_P3','DEMO_OVERDUE_001','030','末道总装终检','F001',3,DATE_SUB(NOW(), INTERVAL 4 DAY),NOW()),

('DEMO_RETURN_P1','DEMO_RETURN_001','010','首道精加工','F002',1,DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),
('DEMO_RETURN_P2','DEMO_RETURN_001','020','二道热处理','F003',2,DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),
('DEMO_RETURN_P3','DEMO_RETURN_001','030','末道总装终检','F001',3,DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),

('DEMO_DONE_P1','DEMO_DONE_001','010','首道精加工','F002',1,DATE_SUB(NOW(), INTERVAL 3 DAY),NOW()),
('DEMO_DONE_P2','DEMO_DONE_001','020','二道热处理','F003',2,DATE_SUB(NOW(), INTERVAL 3 DAY),NOW()),
('DEMO_DONE_P3','DEMO_DONE_001','030','末道总装终检','F001',3,DATE_SUB(NOW(), INTERVAL 3 DAY),NOW());

INSERT INTO process_records(record_id, order_id, process_id, factory_id, record_status, lock_type, total_receive_qty, total_ship_qty, partial_receive, partial_ship, last_receive_time, last_ship_time, created_at, updated_at)
VALUES
-- 初始流程：所有工序未开始，订单 pending
('MADM_R1','MADM_FLOW_001','MADM_P1','F002','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),
('MADM_R2','MADM_FLOW_001','MADM_P2','F003','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),
('MADM_R3','MADM_FLOW_001','MADM_P3','F001','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),

('DEMO_PENDING_R1','DEMO_PENDING_001','DEMO_PENDING_P1','F002','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),
('DEMO_PENDING_R2','DEMO_PENDING_001','DEMO_PENDING_P2','F003','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),
('DEMO_PENDING_R3','DEMO_PENDING_001','DEMO_PENDING_P3','F001','pending','none',0,0,0,0,NULL,NULL,NOW(),NOW()),

-- 首道已接收未发出：只能由 F002 发出到 F003
('DEMO_RECEIVED_R1','DEMO_RECEIVED_001','DEMO_RECEIVED_P1','F002','received','entry_lock',50,0,0,0,DATE_SUB(NOW(), INTERVAL 1 HOUR),NULL,DATE_SUB(NOW(), INTERVAL 2 HOUR),NOW()),
('DEMO_RECEIVED_R2','DEMO_RECEIVED_001','DEMO_RECEIVED_P2','F003','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 2 HOUR),NOW()),
('DEMO_RECEIVED_R3','DEMO_RECEIVED_001','DEMO_RECEIVED_P3','F001','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 2 HOUR),NOW()),

-- 分批流转：首道接收100、分两批发70；二道只接收70，关系已确认，末道未开始
('DEMO_SPLIT_R1','DEMO_SPLIT_001','DEMO_SPLIT_P1','F002','shipped','relation_lock',100,70,1,1,DATE_SUB(NOW(), INTERVAL 5 HOUR),DATE_SUB(NOW(), INTERVAL 3 HOUR),DATE_SUB(NOW(), INTERVAL 6 HOUR),NOW()),
('DEMO_SPLIT_R2','DEMO_SPLIT_001','DEMO_SPLIT_P2','F003','received','entry_lock',70,0,0,0,DATE_SUB(NOW(), INTERVAL 2 HOUR),NULL,DATE_SUB(NOW(), INTERVAL 6 HOUR),NOW()),
('DEMO_SPLIT_R3','DEMO_SPLIT_001','DEMO_SPLIT_P3','F001','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 6 HOUR),NOW()),

-- 超期：首道接收超过48小时未发出
('DEMO_OVERDUE_R1','DEMO_OVERDUE_001','DEMO_OVERDUE_P1','F002','received','entry_lock',60,0,0,0,DATE_SUB(NOW(), INTERVAL 60 HOUR),NULL,DATE_SUB(NOW(), INTERVAL 60 HOUR),NOW()),
('DEMO_OVERDUE_R2','DEMO_OVERDUE_001','DEMO_OVERDUE_P2','F003','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 60 HOUR),NOW()),
('DEMO_OVERDUE_R3','DEMO_OVERDUE_001','DEMO_OVERDUE_P3','F001','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 60 HOUR),NOW()),

-- 退件补发：首道先发80，二道接收80后退10；目前首道剩余70已确认、需补发10，二道有效接收70
('DEMO_RETURN_R1','DEMO_RETURN_001','DEMO_RETURN_P1','F002','shipped','entry_lock',90,70,0,1,DATE_SUB(NOW(), INTERVAL 22 HOUR),DATE_SUB(NOW(), INTERVAL 18 HOUR),DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),
('DEMO_RETURN_R2','DEMO_RETURN_001','DEMO_RETURN_P2','F003','received','entry_lock',70,0,1,0,DATE_SUB(NOW(), INTERVAL 16 HOUR),NULL,DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),
('DEMO_RETURN_R3','DEMO_RETURN_001','DEMO_RETURN_P3','F001','pending','none',0,0,0,0,NULL,NULL,DATE_SUB(NOW(), INTERVAL 1 DAY),NOW()),

-- 已完成：三道均完成，末道完成后订单 completed
('DEMO_DONE_R1','DEMO_DONE_001','DEMO_DONE_P1','F002','completed','sync_lock',120,120,0,0,DATE_SUB(NOW(), INTERVAL 3 DAY),DATE_SUB(NOW(), INTERVAL 2 DAY),DATE_SUB(NOW(), INTERVAL 3 DAY),NOW()),
('DEMO_DONE_R2','DEMO_DONE_001','DEMO_DONE_P2','F003','completed','sync_lock',120,120,0,0,DATE_SUB(NOW(), INTERVAL 2 DAY),DATE_SUB(NOW(), INTERVAL 1 DAY),DATE_SUB(NOW(), INTERVAL 2 DAY),NOW()),
('DEMO_DONE_R3','DEMO_DONE_001','DEMO_DONE_P3','F001','completed','sync_lock',120,120,0,0,DATE_SUB(NOW(), INTERVAL 1 DAY),DATE_SUB(NOW(), INTERVAL 12 HOUR),DATE_SUB(NOW(), INTERVAL 1 DAY),NOW());

INSERT INTO receive_batches(batch_id, record_id, user_id, receive_time, receive_qty, batch_no, return_qty, created_at, updated_at)
VALUES
('DEMO_RB_RECEIVED_1','DEMO_RECEIVED_R1','U004',DATE_SUB(NOW(), INTERVAL 1 HOUR),50,1,0,NOW(),NOW()),

('DEMO_RB_SPLIT_1','DEMO_SPLIT_R1','U004',DATE_SUB(NOW(), INTERVAL 5 HOUR),30,1,0,NOW(),NOW()),
('DEMO_RB_SPLIT_2','DEMO_SPLIT_R1','U004',DATE_SUB(NOW(), INTERVAL 4 HOUR),70,2,0,NOW(),NOW()),
('DEMO_RB_SPLIT_3','DEMO_SPLIT_R2','U005',DATE_SUB(NOW(), INTERVAL 2 HOUR),70,1,0,NOW(),NOW()),

('DEMO_RB_OVERDUE_1','DEMO_OVERDUE_R1','U004',DATE_SUB(NOW(), INTERVAL 60 HOUR),60,1,0,NOW(),NOW()),

('DEMO_RB_RETURN_1','DEMO_RETURN_R1','U004',DATE_SUB(NOW(), INTERVAL 22 HOUR),90,1,0,NOW(),NOW()),
('DEMO_RB_RETURN_2','DEMO_RETURN_R2','U005',DATE_SUB(NOW(), INTERVAL 16 HOUR),80,1,10,NOW(),NOW()),

('DEMO_RB_DONE_1','DEMO_DONE_R1','U004',DATE_SUB(NOW(), INTERVAL 3 DAY),120,1,0,NOW(),NOW()),
('DEMO_RB_DONE_2','DEMO_DONE_R2','U005',DATE_SUB(NOW(), INTERVAL 2 DAY),120,1,0,NOW(),NOW()),
('DEMO_RB_DONE_3','DEMO_DONE_R3','U007',DATE_SUB(NOW(), INTERVAL 1 DAY),120,1,0,NOW(),NOW());

INSERT INTO ship_batches(batch_id, record_id, user_id, ship_time, ship_qty, batch_no, created_at, updated_at)
VALUES
('DEMO_SB_SPLIT_1','DEMO_SPLIT_R1','U004',DATE_SUB(NOW(), INTERVAL 3 HOUR),40,1,NOW(),NOW()),
('DEMO_SB_SPLIT_2','DEMO_SPLIT_R1','U004',DATE_SUB(NOW(), INTERVAL 150 MINUTE),30,2,NOW(),NOW()),

('DEMO_SB_RETURN_1','DEMO_RETURN_R1','U004',DATE_SUB(NOW(), INTERVAL 18 HOUR),80,1,NOW(),NOW()),

('DEMO_SB_DONE_1','DEMO_DONE_R1','U004',DATE_SUB(NOW(), INTERVAL 2 DAY),120,1,NOW(),NOW()),
('DEMO_SB_DONE_2','DEMO_DONE_R2','U005',DATE_SUB(NOW(), INTERVAL 1 DAY),120,1,NOW(),NOW()),
('DEMO_SB_DONE_3','DEMO_DONE_R3','U007',DATE_SUB(NOW(), INTERVAL 12 HOUR),120,1,NOW(),NOW());

INSERT INTO return_records(return_id, from_record_id, to_record_id, user_id, return_reason, return_qty, created_at)
VALUES
('DEMO_RET_RETURN_1','DEMO_RETURN_R1','DEMO_RETURN_R2','U005','热处理硬度不达标，退回首道补加工',10,DATE_SUB(NOW(), INTERVAL 4 HOUR));

INSERT INTO notifications(notif_id, user_id, title, content, notif_type, is_read, related_id, related_type, jump_url, created_at)
VALUES
('DEMO_N_U001_1','U001','系统测试数据已刷新','外协流转模拟数据已清空并重新生成，中文通知显示正常。','other',0,'DEMO_PENDING_001','order','/kanban/DEMO_PENDING_001',NOW()),
('DEMO_N_U001_2','U001','超期订单提醒','订单 DEMO_OVERDUE_001 首道精加工已接收60件，超过48小时未发出。','transfer',0,'DEMO_OVERDUE_001','order','/kanban/DEMO_OVERDUE_001',DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
('DEMO_N_U004_1','U004','待发出提醒','订单 DEMO_RECEIVED_001 首道精加工已接收50件，请发往热处理B厂。','transfer',0,'DEMO_RECEIVED_001','order','/kanban/DEMO_RECEIVED_001',DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
('DEMO_N_U004_2','U004','退件补发提醒','订单 DEMO_RETURN_001 热处理B厂退回10件，需补发合格件。','approval',1,'DEMO_RETURN_001','order','/kanban/DEMO_RETURN_001',DATE_SUB(NOW(), INTERVAL 3 HOUR)),
('DEMO_N_U005_1','U005','下道待处理','订单 DEMO_SPLIT_001 已从精加工A厂分两批发出70件，并由热处理B厂接收。','transfer',0,'DEMO_SPLIT_001','order','/kanban/DEMO_SPLIT_001',DATE_SUB(NOW(), INTERVAL 2 HOUR)),
('DEMO_N_U005_2','U005','退件记录','已退回10件：热处理硬度不达标，退回首道补加工。','approval',1,'DEMO_RETURN_001','order','/kanban/DEMO_RETURN_001',DATE_SUB(NOW(), INTERVAL 4 HOUR)),
('DEMO_N_U007_1','U007','末道待接收','订单 DEMO_DONE_001 已完成归档；订单 DEMO_SPLIT_001 末道尚未接收。','transfer',0,'DEMO_SPLIT_001','order','/kanban/DEMO_SPLIT_001',DATE_SUB(NOW(), INTERVAL 1 HOUR));

INSERT INTO action_logs(log_id, user_id, action_type, target_table, target_id, old_value, new_value, ip_address, created_at)
VALUES
('DEMO_LOG_1','U001','DEMO_DATA_RESET','orders','DEMO_PENDING_001',NULL,JSON_OBJECT('status','created','charset','utf8mb4'),'127.0.0.1',NOW()),
('DEMO_LOG_2','U004','RECEIVE','process_records','DEMO_RECEIVED_R1',NULL,JSON_OBJECT('qty',50),'127.0.0.1',DATE_SUB(NOW(), INTERVAL 1 HOUR)),
('DEMO_LOG_3','U004','SHIP','process_records','DEMO_SPLIT_R1',NULL,JSON_OBJECT('qty',70,'batches',2),'127.0.0.1',DATE_SUB(NOW(), INTERVAL 150 MINUTE)),
('DEMO_LOG_4','U005','RETURN','return_records','DEMO_RET_RETURN_1',NULL,JSON_OBJECT('qty',10,'reason','热处理硬度不达标'),'127.0.0.1',DATE_SUB(NOW(), INTERVAL 4 HOUR));
"""

VERIFY_SQL = r"""
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT 'factories' AS item, COUNT(*) AS count FROM factories;
SELECT 'users' AS item, COUNT(*) AS count FROM users;
SELECT 'orders' AS item, COUNT(*) AS count FROM orders;
SELECT 'processes' AS item, COUNT(*) AS count FROM processes;
SELECT 'records' AS item, COUNT(*) AS count FROM process_records;
SELECT 'receive_batches' AS item, COUNT(*) AS count FROM receive_batches;
SELECT 'ship_batches' AS item, COUNT(*) AS count FROM ship_batches;
SELECT 'return_records' AS item, COUNT(*) AS count FROM return_records;
SELECT 'notifications' AS item, COUNT(*) AS count FROM notifications;

SELECT order_id, product_name, product_code, spec, unit, part_no, delivery_date, order_status, total_qty FROM orders ORDER BY order_id;
SELECT pr.order_id, p.process_order, pr.record_id, p.factory_id, pr.record_status, pr.lock_type,
       pr.total_receive_qty, pr.total_ship_qty, pr.partial_receive, pr.partial_ship
FROM process_records pr
JOIN processes p ON p.process_id = pr.process_id
ORDER BY pr.order_id, p.process_order;
SELECT notif_id, user_id, title, content FROM notifications ORDER BY created_at DESC LIMIT 5;
"""

CONSISTENCY_SQL = r"""
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT 'order_without_3_processes' AS check_name, COUNT(*) AS bad_count
FROM orders o
LEFT JOIN (SELECT order_id, COUNT(*) c FROM processes GROUP BY order_id) p ON p.order_id=o.order_id
WHERE p.c <> 3 OR p.c IS NULL;

SELECT 'order_status_mismatch' AS check_name, COUNT(*) AS bad_count
FROM orders o
JOIN (
  SELECT order_id,
         CASE
           WHEN SUM(record_status <> 'completed') = 0 THEN 'completed'
           WHEN SUM(record_status IN ('received','shipped')) > 0 THEN 'in_progress'
           ELSE 'pending'
         END AS expected_status
  FROM process_records GROUP BY order_id
) x ON x.order_id=o.order_id
WHERE o.order_status <> x.expected_status;

SELECT 'record_qty_invalid' AS check_name, COUNT(*) AS bad_count
FROM process_records
WHERE total_receive_qty < 0 OR total_ship_qty < 0 OR total_ship_qty > total_receive_qty;

SELECT 'downstream_receive_exceeds_prev_ship' AS check_name, COUNT(*) AS bad_count
FROM process_records curr
JOIN processes cp ON cp.process_id=curr.process_id
JOIN processes pp ON pp.order_id=cp.order_id AND pp.process_order=cp.process_order-1
JOIN process_records prev ON prev.process_id=pp.process_id
WHERE curr.total_receive_qty > prev.total_ship_qty;

SELECT 'mojibake_notifications' AS check_name, COUNT(*) AS bad_count
FROM notifications
WHERE title REGEXP 'Ã|Â|â|�|ç|æ|è|ä' OR content REGEXP 'Ã|Â|â|�|ç|æ|è|ä';
"""


def main() -> None:
    ensure_order_columns()
    ensure_notification_columns()
    mysql(SQL)
    verification = mysql(VERIFY_SQL)
    consistency = mysql(CONSISTENCY_SQL)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok",
        "mysql_client_charset": "utf8mb4",
        "login_phones": {
            "enterprise_admin": "13800138000",
            "primary_admin": "13800138001",
            "a_factory_operator": "13800138003",
            "b_factory_operator": "13800138004",
            "b_factory_admin": "13800138005",
            "final_process_operator": "13800138006",
            "surface_operator": "13800138007",
        },
        "qr_codes_for_manual_test": {
            "receive_page": "record_DEMO_PENDING_R1",
            "ship_page": "record_DEMO_RECEIVED_R1",
            "view_page": "record_DEMO_SPLIT_R1",
            "overdue_ship_page": "record_DEMO_OVERDUE_R1",
            "return_rework_page": "record_DEMO_RETURN_R1",
            "done_view_page": "record_DEMO_DONE_R1",
            "main_flow_receive": "record_MADM_R1",
        },
        "orders": [
            "MADM_FLOW_001",
            "DEMO_PENDING_001",
            "DEMO_RECEIVED_001",
            "DEMO_SPLIT_001",
            "DEMO_OVERDUE_001",
            "DEMO_RETURN_001",
            "DEMO_DONE_001",
        ],
        "verification_raw": verification,
        "consistency_raw": consistency,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"RESULT_FILE={OUT}")


if __name__ == "__main__":
    main()
