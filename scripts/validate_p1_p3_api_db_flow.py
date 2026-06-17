#!/usr/bin/env python3
"""P1-P3 动态交叉验证：MOM/标准文件导入 + DB 回查 + 权限 + 审计报表。"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost:8000"
API = f"{BASE}/api"
ORDER_ID = "P1P3_API_001"
BATCH_NO = "P1P3-BATCH-001"
PROCESS_IDS = ["P1P3_PROC_010", "P1P3_PROC_020", "P1P3_PROC_030"]
RECORD_IDS = [f"REC-{pid}" for pid in PROCESS_IDS]
OUT_JSON = ROOT / "docs" / "acceptance" / "p1-p3-api-db-validation-result.json"
OUT_MD = ROOT / "docs" / "acceptance" / "P1-P3阶段动态交叉验证报告-2026-06-17.md"

HTTP = requests.Session()
HTTP.trust_env = False

results: list[dict] = []
errors: list[str] = []


def run(cmd: list[str], *, input_text: str | None = None, check: bool = True) -> str:
    p = subprocess.run(cmd, cwd=ROOT, input=input_text, text=True, encoding="utf-8", capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"CMD failed: {' '.join(cmd)}\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}")
    return p.stdout.strip()


def sql(query: str) -> str:
    return run([
        "docker", "exec", "-i", "outsourcing-track-mysql-1", "sh", "-lc",
        'mysql --default-character-set=utf8mb4 -uroot -p"$MYSQL_ROOT_PASSWORD" outsourcing_track --batch --raw --skip-column-names',
    ], input_text=query)


def add(name: str, ok: bool, expected: str, actual) -> None:
    results.append({"name": name, "pass": bool(ok), "expected": expected, "actual": actual})
    if not ok:
        errors.append(name)


def api(method: str, path: str, token: str | None = None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = HTTP.request(method, API + path, headers=headers, timeout=20, **kwargs)
    try:
        body = r.json()
    except Exception:
        body = r.content
    return r.status_code, body, r.headers


def login(phone: str) -> str:
    code, body, _ = api("POST", "/auth/send-sms", json={"phone": phone})
    assert code == 200, (phone, code, body)
    code, body, _ = api("POST", "/auth/login", json={"phone": phone, "code": body["code"]})
    assert code == 200, (phone, code, body)
    return body["access_token"]


def reset_data() -> None:
    quoted_records = ",".join(f"'{x}'" for x in RECORD_IDS)
    quoted_processes = ",".join(f"'{x}'" for x in PROCESS_IDS)
    sql(f"""
    SET FOREIGN_KEY_CHECKS=0;
    DELETE FROM action_logs WHERE target_id='{BATCH_NO}' OR target_id='{ORDER_ID}' OR target_id IN ({quoted_records}) OR target_id IN ({quoted_processes});
    DELETE FROM return_records WHERE from_record_id IN ({quoted_records}) OR to_record_id IN ({quoted_records});
    DELETE FROM receive_batches WHERE record_id IN ({quoted_records});
    DELETE FROM ship_batches WHERE record_id IN ({quoted_records});
    DELETE FROM process_records WHERE record_id IN ({quoted_records}) OR order_id='{ORDER_ID}';
    DELETE FROM processes WHERE process_id IN ({quoted_processes}) OR order_id='{ORDER_ID}';
    DELETE FROM orders WHERE order_id='{ORDER_ID}';
    SET FOREIGN_KEY_CHECKS=1;
    """)


def db_snapshot() -> str:
    return sql(f"""
    SELECT COUNT(*) FROM orders WHERE order_id='{ORDER_ID}';
    SELECT COUNT(*) FROM processes WHERE order_id='{ORDER_ID}';
    SELECT COUNT(*) FROM process_records WHERE order_id='{ORDER_ID}';
    SELECT action_type, target_table, target_id FROM action_logs WHERE target_id='{BATCH_NO}' ORDER BY created_at DESC LIMIT 1;
    SELECT pr.record_id, p.process_seq, pr.record_status, pr.lock_type, pr.total_receive_qty, pr.total_ship_qty
    FROM process_records pr JOIN processes p ON pr.process_id=p.process_id
    WHERE pr.order_id='{ORDER_ID}' ORDER BY p.process_order;
    """)


def main() -> None:
    started_at = datetime.now().isoformat(timespec="seconds")
    try:
        health = HTTP.get(f"{BASE}/health", timeout=10)
        add("后端健康检查", health.status_code == 200, "HTTP 200", health.status_code)

        reset_data()
        enterprise = login("13800138000")
        primary_admin = login("13800138001")
        operator = login("13800138003")

        payload = {
            "source_type": "standard_file",
            "batch_no": BATCH_NO,
            "orders": [{
                "order_id": ORDER_ID,
                "primary_factory_id": "F002",
                "product_name": "P1P3标准文件导入测试件",
                "product_code": "P1P3-CODE",
                "spec": "API+DB交叉验证",
                "unit": "件",
                "part_no": "P1P3-PART",
                "total_qty": 36,
                "delivery_date": "2026-07-01",
                "mom_created_at": "2026-06-17T00:00:00",
                "processes": [
                    {"process_id": PROCESS_IDS[0], "process_seq": "010", "process_name": "粗加工", "factory_id": "F002", "process_order": 1},
                    {"process_id": PROCESS_IDS[1], "process_seq": "020", "process_name": "热处理", "factory_id": "F003", "process_order": 2},
                    {"process_id": PROCESS_IDS[2], "process_seq": "030", "process_name": "终检", "factory_id": "F001", "process_order": 3},
                ],
            }],
        }

        code, body, _ = api("POST", "/mom/orders/import", token=enterprise, json=payload)
        add("企业管理员导入MOM标准文件", code == 200 and body.get("created_orders") == 1 and body.get("created_records") == 3, "200且创建1订单/3记录", {"code": code, "body": body})

        code2, body2, _ = api("POST", "/mom/orders/import", token=operator, json={**payload, "batch_no": BATCH_NO + "-DENY", "dry_run": True})
        add("普通操作员禁止导入", code2 == 403, "HTTP 403", {"code": code2, "body": body2})

        code3, body3, _ = api("POST", "/mom/orders/import", token=primary_admin, json={**payload, "batch_no": BATCH_NO + "-DRY", "dry_run": True})
        add("主厂管理员允许导入DryRun", code3 == 200, "HTTP 200", {"code": code3, "body": body3})

        snapshot = db_snapshot()
        lines = snapshot.splitlines()
        add("DB回查订单/工序/记录/审计日志", len(lines) >= 7 and lines[0] == "1" and lines[1] == "3" and lines[2] == "3" and "MOM_IMPORT" in lines[3], "订单1/工序3/记录3/日志MOM_IMPORT", snapshot)

        code4, logs, _ = api("GET", "/audit/logs?action_type=MOM_IMPORT&page_size=5", token=enterprise)
        add("审计日志接口可查MOM导入", code4 == 200 and logs.get("total", 0) >= 1, "HTTP 200且total>=1", {"code": code4, "body": logs})

        code5, summary, _ = api("GET", "/audit/summary", token=enterprise)
        add("审计汇总接口可统计", code5 == 200 and summary.get("total_logs", 0) >= 1, "HTTP 200且total_logs>=1", {"code": code5, "body": summary})

        code6, export_body, headers = api("GET", "/audit/export?action_type=MOM_IMPORT", token=enterprise)
        add("审计Excel导出", code6 == 200 and isinstance(export_body, (bytes, bytearray)) and len(export_body) > 1000, "HTTP 200且xlsx非空", {"code": code6, "size": len(export_body) if isinstance(export_body, (bytes, bytearray)) else 0, "content_type": headers.get("content-type")})

        code7, denied, _ = api("GET", "/audit/logs", token=operator)
        add("普通操作员禁止访问审计API", code7 == 403, "HTTP 403", {"code": code7, "body": denied})

    except Exception as exc:
        errors.append(repr(exc))

    report = {
        "started_at": started_at,
        "order_id": ORDER_ID,
        "summary": {"total": len(results), "passed": sum(1 for r in results if r["pass"]), "failed": sum(1 for r in results if not r["pass"])},
        "results": results,
        "errors": errors,
        "db_snapshot": db_snapshot() if not errors else "",
        "note": "飞书接入已取消；本验证仅覆盖MOM/标准文件导入、权限、DB与审计报表。",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# P1-P3阶段动态交叉验证报告\n\n",
        f"生成时间：{started_at}\n\n",
        f"订单样本：`{ORDER_ID}`\n\n",
        f"结论：总项 {report['summary']['total']}，通过 {report['summary']['passed']}，失败 {report['summary']['failed']}。\n\n",
        "说明：飞书接入已取消；本轮按 MOM/标准文件数据源验收。\n\n",
        "## 检查项\n",
    ]
    for item in results:
        mark = "✅" if item["pass"] else "❌"
        lines.append(f"- {mark} {item['name']}\n")
    if errors:
        lines.append("\n## 错误\n")
        for e in errors:
            lines.append(f"- {e}\n")
    lines.append("\n## DB快照\n\n```text\n" + report.get("db_snapshot", "") + "\n```\n")
    OUT_MD.write_text("".join(lines), encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"RESULT_JSON={OUT_JSON}")
    print(f"RESULT_MD={OUT_MD}")
    if report["summary"]["failed"] or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
