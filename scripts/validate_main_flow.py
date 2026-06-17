#!/usr/bin/env python3
"""
MADM-Solo Phase 4: 外协工序主流程真实 API + DB 验收脚本
验证：登录 → 看板 → 首道接收 → 分批接收 → 发出 → 下道接收 → DB核对
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = "http://localhost:8000"
API = f"{BASE}/api"
LOCAL_HTTP = requests.Session()
LOCAL_HTTP.trust_env = False
ORDER_ID = "MADM_FLOW_001"
P1, P2, P3 = "MADM_P1", "MADM_P2", "MADM_P3"
R1, R2, R3 = "MADM_R1", "MADM_R2", "MADM_R3"

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, check=True, *, input_text=None):
    p = subprocess.run(cmd, cwd=ROOT, input=input_text, text=True, encoding="utf-8", capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"CMD failed: {' '.join(cmd)}\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}")
    return p.stdout.strip()


def sql(query):
    """Run SQL through the mysql container using utf8mb4 and container env password.

    Passing SQL via stdin avoids shell escaping issues and prevents printing DB credentials.
    """
    return run([
        "docker", "exec", "-i", "outsourcing-track-mysql-1", "sh", "-lc",
        'mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" outsourcing_track --batch --raw --skip-column-names',
    ], input_text=query)


def api(method, path, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = LOCAL_HTTP.request(method, f"{API}{path}", headers=headers, timeout=10, **kwargs)
    try:
        body = r.json()
    except Exception:
        body = r.text
    return r.status_code, body


def login(phone):
    code, body = api("POST", "/auth/send-sms", json={"phone": phone})
    assert code == 200, ("send-sms", code, body)
    sms_code = body["code"]
    code, body = api("POST", "/auth/login", json={"phone": phone, "code": sms_code})
    assert code == 200, ("login", phone, code, body)
    return body["access_token"]


def record_state():
    q = f"""
    SELECT pr.record_id, p.process_order, pr.record_status, pr.lock_type,
           pr.total_receive_qty, pr.total_ship_qty, pr.partial_receive, pr.partial_ship
    FROM process_records pr JOIN processes p ON pr.process_id=p.process_id
    WHERE pr.order_id='{ORDER_ID}'
    ORDER BY p.process_order;
    SELECT order_status FROM orders WHERE order_id='{ORDER_ID}';
    SELECT COUNT(*) FROM receive_batches WHERE record_id IN ('{R1}','{R2}','{R3}');
    SELECT COUNT(*) FROM ship_batches WHERE record_id IN ('{R1}','{R2}','{R3}');
    """
    return sql(q)


def reset_data():
    q = f"""
    SET FOREIGN_KEY_CHECKS=0;
    DELETE FROM action_logs WHERE target_id IN ('{R1}','{R2}','{R3}','{ORDER_ID}') OR target_id IN (SELECT batch_id FROM receive_batches WHERE record_id IN ('{R1}','{R2}','{R3}')) OR target_id IN (SELECT batch_id FROM ship_batches WHERE record_id IN ('{R1}','{R2}','{R3}'));
    DELETE FROM return_records WHERE from_record_id IN ('{R1}','{R2}','{R3}') OR to_record_id IN ('{R1}','{R2}','{R3}');
    DELETE FROM receive_batches WHERE record_id IN ('{R1}','{R2}','{R3}');
    DELETE FROM ship_batches WHERE record_id IN ('{R1}','{R2}','{R3}');
    DELETE FROM process_records WHERE order_id='{ORDER_ID}';
    DELETE FROM processes WHERE order_id='{ORDER_ID}';
    DELETE FROM orders WHERE order_id='{ORDER_ID}';
    SET FOREIGN_KEY_CHECKS=1;

    INSERT INTO orders(order_id, primary_factory_id, order_status, total_qty, mom_created_at)
    VALUES('{ORDER_ID}', 'F002', 'pending', 100, NOW());
    INSERT INTO processes(process_id, order_id, process_seq, process_name, factory_id, process_order)
    VALUES
      ('{P1}', '{ORDER_ID}', '010', 'MADM首道', 'F002', 1),
      ('{P2}', '{ORDER_ID}', '020', 'MADM二道', 'F003', 2),
      ('{P3}', '{ORDER_ID}', '030', 'MADM末道', 'F001', 3);
    INSERT INTO process_records(record_id, order_id, process_id, factory_id, record_status, lock_type, total_receive_qty, total_ship_qty)
    VALUES
      ('{R1}', '{ORDER_ID}', '{P1}', 'F002', 'pending', 'none', 0, 0),
      ('{R2}', '{ORDER_ID}', '{P2}', 'F003', 'pending', 'none', 0, 0),
      ('{R3}', '{ORDER_ID}', '{P3}', 'F001', 'pending', 'none', 0, 0);
    """
    sql(q)


def assert_status(name, actual, expected):
    ok = actual == expected
    results.append({"name": name, "pass": ok, "actual": actual, "expected": expected})
    if not ok:
        raise AssertionError(f"{name}: expected {expected}, actual {actual}")


results = []
errors = []
start = datetime.now().isoformat(timespec="seconds")

try:
    # health
    hr = LOCAL_HTTP.get(f"{BASE}/health", timeout=10)
    assert_status("Backend health", hr.status_code, 200)

    reset_data()
    initial = record_state()

    token_f2 = login("13800138003")  # F002 操作员
    token_f3 = login("13800138004")  # F003 操作员
    token_f1 = login("13800138000")  # F001 企业管理员

    code, body = api("GET", "/kanban/orders", token_f2)
    assert_status("看板订单接口", code, 200)

    # 首道首次接收 40：预期成功，R1 entry_lock，订单 in_progress
    code, body = api("POST", "/records/receive", token_f2, json={"record_id": R1, "receive_qty": 40})
    assert_status("R1 首次接收 API", code, 200)
    state_after_r1_receive = record_state()

    # 首道分批接收 60：理想业务应允许；当前旧逻辑若 entry_lock 阻断则失败
    code, body = api("POST", "/records/receive", token_f2, json={"record_id": R1, "receive_qty": 60})
    split_receive_code, split_receive_body = code, body
    if code == 200:
        results.append({"name": "R1 分批接收 API", "pass": True, "actual": code, "expected": 200})
    else:
        results.append({"name": "R1 分批接收 API", "pass": False, "actual": {"code": code, "body": body}, "expected": 200})

    state_after_split = record_state()

    # 尝试发出：如果分批失败，只发出 40；若 entry_lock 仍阻断会暴露死锁
    ship_qty = 100 if split_receive_code == 200 else 40
    code, body = api("POST", "/records/ship", token_f2, json={"record_id": R1, "ship_qty": ship_qty})
    ship_r1_code, ship_r1_body = code, body
    if code == 200:
        results.append({"name": "R1 发出 API", "pass": True, "actual": code, "expected": 200})
    else:
        results.append({"name": "R1 发出 API", "pass": False, "actual": {"code": code, "body": body}, "expected": 200})

    state_after_r1_ship = record_state()

    # 如果 R1 发出成功，验证 R2 接收及 R1 自动 relation_lock
    downstream = None
    if ship_r1_code == 200:
        code, body = api("POST", "/records/receive", token_f3, json={"record_id": R2, "receive_qty": ship_qty})
        downstream = {"code": code, "body": body}
        results.append({"name": "R2 下道接收 API", "pass": code == 200, "actual": downstream, "expected": 200})

    # 下道接收后发起退件：真实业务中接收方发现问题后退回上一道
    return_result = None
    if ship_r1_code == 200 and downstream and downstream.get("code") == 200:
        code, body = api("POST", "/records/return", token_f3, json={
            "from_record_id": R1,
            "to_record_id": R2,
            "return_qty": 10,
            "return_reason": "MADM验收退件"
        })
        return_result = {"code": code, "body": body}
        results.append({"name": "R2 退件回 R1 API", "pass": code == 200, "actual": return_result, "expected": 200})

    final_state = record_state()

except Exception as e:
    errors.append(repr(e))
    final_state = record_state() if 'record_state' in globals() else ''

report = {
    "started_at": start,
    "order_id": ORDER_ID,
    "results": results,
    "errors": errors,
    "final_db_state": final_state,
    "notes": {
        "split_receive_response": locals().get("split_receive_body", None),
        "ship_r1_response": locals().get("ship_r1_body", None),
        "initial_db_state": locals().get("initial", None),
        "after_r1_receive": locals().get("state_after_r1_receive", None),
        "after_split": locals().get("state_after_split", None),
        "after_r1_ship": locals().get("state_after_r1_ship", None),
        "downstream": locals().get("downstream", None),
    }
}

out = ROOT / "docs" / "acceptance" / "main-flow-validation-result.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"\nRESULT_FILE={out}")

failed = [r for r in results if not r.get("pass")]
sys.exit(1 if failed or errors else 0)
