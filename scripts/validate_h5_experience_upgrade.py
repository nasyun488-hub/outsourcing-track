#!/usr/bin/env python3
"""H5 全页面体验升级静态契约验证。

验证目标来自 .hermes/plans/2026-06-16_全页面功能人机交互优化方案.md：
除扫码页外，登录、首页、看板、详情、接收/发出、记录、通知、管理、导出页必须有明确的
“先给结论、任务流组织、移动端少输入、异常可追踪”的体验改造痕迹。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "frontend" / "src" / "views"

CHECKS: dict[str, list[str]] = {
    "LoginPage.vue": [
        "外协工序流转追踪｜扫码记录每一道流转",
        "演示环境提示",
        "收不到验证码",
        "测试验证码已自动填入",
        "账号密码登录",
        "手机号/账号",
        "passwordLogin",
        "验证码已过期，请重新获取",
    ],
    "HomePage.vue": [
        "今日待办",
        "开始扫码录入",
        "查看待接收",
        "查看待发出",
        "逾期工序，请优先处理",
        "按现场一天工作节奏",
    ],
    "KanbanPage.vue": [
        "外协流转雷达",
        "我厂相关",
        "待我处理",
        "已逾期",
        "今日更新",
        "即将超期",
        "当前卡点",
        "流转进度",
    ],
    "KanbanDetailPage.vue": [
        "订单作战室",
        "下一步建议",
        "工序流转时间线",
        "等待上道发出",
        "可接收",
        "可发出",
    ],
    "ReceivePage.vue": [
        "接收操作台",
        "本次可接收",
        "一键填入全部可接收数量",
        "提交后返回订单详情",
        "不可接收原因",
    ],
    "ShipPage.vue": [
        "发出操作台",
        "本次可发出",
        "一键填入全部可发出数量",
        "退件不打断主流程",
        "提交后返回订单详情",
    ],
    "RecordViewPage.vue": [
        "流转凭证",
        "关联订单",
        "当前工序状态",
        "返回订单详情",
        "扫码来源可追溯",
    ],
    "NotificationPage.vue": [
        "异常队列",
        "先处理高风险",
        "全部已读",
        "跳转处理",
        "通知即待办",
    ],
    "AdminUserPage.vue": [
        "人员权限控制台",
        "待审核队列",
        "角色权限说明",
        "操作员必须绑定厂家",
        "启用/禁用",
    ],
    "AdminFactoryPage.vue": [
        "厂家协作控制台",
        "厂家审核队列",
        "联系人与手机号",
        "合作状态",
        "新增厂家后可分配人员",
    ],
    "ExportPage.vue": [
        "报表导出中心",
        "导出预览",
        "常用报表",
        "今天",
        "本周",
        "本月",
        "导出文件包含",
    ],
}


def main() -> int:
    failures: list[str] = []
    for filename, needles in CHECKS.items():
        path = VIEWS / filename
        if not path.exists():
            failures.append(f"{filename}: 文件不存在")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                failures.append(f"{filename}: 缺少体验契约文案/结构 `{needle}`")

    if failures:
        print("H5 experience contract FAILED")
        for item in failures:
            print("-", item)
        return 1

    print("H5 experience contract OK")
    print(f"checked_pages={len(CHECKS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
