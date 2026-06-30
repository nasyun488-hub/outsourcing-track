#!/usr/bin/env python3
"""PC 端体验优化契约检查：覆盖 PC Shell、看板、审计、导出、人员/厂家管理。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"缺少 {label}: {needle}")


def main() -> None:
    app = read(FRONTEND / "App.vue")
    home = read(FRONTEND / "views" / "HomePage.vue")
    kanban = read(FRONTEND / "views" / "KanbanPage.vue")
    audit = read(FRONTEND / "views" / "AuditReportPage.vue")
    export = read(FRONTEND / "views" / "ExportPage.vue")
    users = read(FRONTEND / "views" / "AdminUserPage.vue")
    factories = read(FRONTEND / "views" / "AdminFactoryPage.vue")
    api = read(FRONTEND / "api" / "kanban.ts")
    router = read(BACKEND / "routers" / "kanban.py")
    service = read(BACKEND / "services" / "kanban_service.py")

    # PC 专用框架：非登录页应有左侧导航、顶部栏、内容区，不再只是 router-view 直出。
    require(app, "pc-shell", "PC应用壳")
    require(app, "side-nav", "PC左侧导航")
    require(app, "topbar", "PC顶部栏")
    require(app, "main-content", "PC内容区")
    require(app, "企业看板", "左侧导航中文菜单")

    # 角色中文化，不能把 primary_admin/cooperative_operator 直接显示给业务用户。
    require(home, "primary_admin: '主厂管理员'", "主厂管理员中文角色")
    require(home, "primary_operator: '主厂操作员'", "主厂操作员中文角色")
    require(home, "cooperative_admin: '协作厂管理员'", "协作厂管理员中文角色")
    require(home, "cooperative_operator: '协作厂操作员'", "协作厂操作员中文角色")

    # 看板快捷筛选必须触发 reload，避免只做前端二次过滤导致统计/列表不一致。
    require(kanban, "async function selectQuick", "异步快捷筛选")
    require(kanban, "await reload()", "快捷筛选触发后端重载")
    require(kanban, "quick", "看板 API quick 参数")
    require(api, "quick?: string", "API quick 参数类型")

    # PC 深度优化：高频办公页必须有桌面表格/工具条，不只是一列手机卡片。
    for text, label in [
        (kanban, "看板PC表格视图"),
        (audit, "审计PC表格视图"),
        (export, "导出PC工作台"),
        (users, "人员管理PC表格视图"),
        (factories, "厂家管理PC表格视图"),
    ]:
        require(text, "pc-data-table", label)
        require(text, "pc-toolbar", f"{label}工具条")
        require(text, "mobile-only", f"{label}移动端兼容")
        require(text, "desktop-only", f"{label}桌面端专用")

    require(kanban, "viewMode", "看板卡片/表格双视图状态")
    require(kanban, "table-view", "看板表格模式切换")
    require(audit, "审计明细表", "审计PC表格标题")
    require(export, "一键导出", "导出PC高频操作")
    require(users, "人员清单表", "人员管理PC表格标题")
    require(factories, "厂家清单表", "厂家管理PC表格标题")
    require(users, "keyword", "人员管理PC关键词搜索")
    require(users, "filterStatus", "人员管理PC状态筛选")
    require(users, "toggleUserSelection", "人员管理PC批量选择")
    require(users, "batchApproveSelected", "人员管理PC批量审核")
    require(factories, "keyword", "厂家管理PC关键词搜索")
    require(factories, "filterStatus", "厂家管理PC状态筛选")
    require(factories, "toggleFactorySelection", "厂家管理PC批量选择")
    require(factories, "batchApproveSelected", "厂家管理PC批量审核")
    require(export, "orderKeyword", "导出PC订单快速输入")
    require(export, "filterForm.factory_id", "导出PC厂家下拉选择")
    require(audit, "selectedLog", "审计PC详情抽屉")
    require(audit, "target_table", "审计PC对象字段")

    # 后端 stats 必须接收 current_user 并复用可见订单口径，避免首页统计与看板列表不一致。
    require(router, "current_user=current_user", "stats 路由传当前用户")
    require(service, "current_user=None", "stats 服务接收当前用户")
    require(service, "_visible_orders_query", "订单列表/统计共用可见口径")

    print("PC UX contract OK")


if __name__ == "__main__":
    main()
