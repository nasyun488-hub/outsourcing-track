#!/usr/bin/env python3
"""角色权限矩阵静态校验。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MATRIX = {
    "enterprise_admin": {"mom_import": True, "audit_report": True},
    "primary_admin": {"mom_import": True, "audit_report": True},
    "primary_operator": {"mom_import": False, "audit_report": False},
    "cooperative_admin": {"mom_import": False, "audit_report": False},
    "cooperative_operator": {"mom_import": False, "audit_report": False},
}


def main() -> None:
    errors: list[str] = []
    mom_router = (ROOT / "backend/app/routers/mom.py").read_text(encoding="utf-8")
    router = (ROOT / "frontend/src/router.ts").read_text(encoding="utf-8")

    if "require_import_permission" not in mom_router:
        errors.append("MOM导入缺少require_import_permission")
    for role in ("enterprise_admin", "primary_admin"):
        if role not in mom_router:
            errors.append(f"MOM导入未允许{role}")
    if "allowedRoles" not in router or "'/audit'" not in router:
        errors.append("前端审计路由缺少角色入口控制")

    print(json.dumps({"matrix": MATRIX, "errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
