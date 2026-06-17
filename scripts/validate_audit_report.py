#!/usr/bin/env python3
"""审计报表静态契约校验。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/routers/audit.py": ["/logs", "/summary", "/export", "StreamingResponse", "get_current_user"],
    "backend/app/services/audit_service.py": ["list_logs", "get_summary", "export_logs", "ActionLog", "openpyxl"],
    "frontend/src/views/AuditReportPage.vue": ["操作审计报表", "审计总览", "导出审计Excel", "/audit/logs", "/audit/summary"],
}


def main() -> None:
    errors: list[str] = []
    for rel, snippets in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"缺少文件: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{rel} 缺少 {snippet}")
    print(json.dumps({"total_errors": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
