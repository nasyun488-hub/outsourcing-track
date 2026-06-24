# 外协工序流转追踪系统 — SDD 开发文档总览

**版本**：v1.0  
**基线**：commit 9cc5f7d (tag: baseline-h5-scan-2026-06-16)  
**日期**：2026-06-18

---

## 文档集清单

| 文档 | 文件名 | 说明 |
|------|-------|------|
| 00 总览与当前状态 | `00-SDD总览与当前状态.md` | 本文档，基线、范围、文档地图 |
| 01 需求规格对应关系 | `01-需求规格对应关系.md` | SPEC → 代码实现映射 |
| 02 系统设计说明 | `02-系统设计说明.md` | 架构、技术栈、模块划分 |
| 03 数据与接口契约 | `03-数据与接口契约.md` | 核心表、API 契约 |
| 04 业务流程与规则算法详解 | `04-业务流程与规则算法详解.md` | 按场景详解流程与算法 |
| 05 实施任务与代码地图 | `05-实施任务与代码地图.md` | 已完成任务、代码索引 |
| 06 测试验收规范 | `06-测试验收规范.md` | 测试环境、验证矩阵、命令 |
| 07 部署运维说明 | `07-部署运维说明.md` | Docker 部署、故障排查 |

---

## 当前基线状态

### 代码基线
- 分支：`master`
- Commit：`9cc5f7d`
- Tag：`baseline-h5-scan-2026-06-16`
- 提交信息：`baseline: H5 experience and scan cart validated state`

### 已部署服务状态
| 服务 | 地址 | 状态 |
|------|------|------|
| 后端 API | `http://localhost:8000` | ✅ 运行中，`/health` 返回 200 |
| 前端 H5 | `http://localhost:8081` | ✅ 运行中，首页返回 200 |
| MySQL | `localhost:3306` | ✅ 运行中，容器 `outsourcing-track-mysql-1` |

### 已验证范围
- ✅ Python 编译检查：`python3 -m compileall -q backend/app scripts` 通过
- ✅ 单元测试：`pytest backend/tests/ -q` 13 项全部通过
- ✅ 前端构建：`npm run build` 通过
- ✅ Docker 构建：`docker compose build frontend` 通过
- ✅ H5 辅助遍历：`python3 scripts/human_ui_traversal.py` 66 项通过
- ✅ 主流程验证：`python3 scripts/validate_main_flow.py` 通过
- ✅ 扫码购物车契约：`python3 scripts/validate_scan_cart_ui.py` 通过
- ✅ 浏览器实测：登录、看板、详情、扫码页无 JS 错误

### 未验证边界
- ⚠️ 真实手机摄像头扫码的像素级全路径验收（浏览器模拟扫码已验证）
- ⚠️ 大规模并发压测（当前按 50 并发设计）

---

## 项目结构

```
/home/takemehome/outsourcing-track/
├── backend/                    # 后端 FastAPI
│   ├── app/
│   │   ├── routers/            # API 路由
│   │   │   ├── auth.py         # 认证登录
│   │   │   ├── kanban.py       # 订单看板
│   │   │   ├── records.py      # 流转记录
│   │   │   ├── notifications.py # 通知
│   │   │   ├── admin.py        # 管理功能
│   │   │   └── export.py       # 导出
│   │   ├── services/           # 业务逻辑
│   │   │   ├── auth_service.py
│   │   │   ├── kanban_service.py
│   │   │   ├── record_service.py
│   │   │   ├── notification_service.py
│   │   │   └── user_service.py
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── core/               # 核心配置、数据库、JWT
│   │   └── main.py             # 应用入口
│   ├── tests/                  # 单元测试
│   └── Dockerfile
├── frontend/                   # 前端 Vue3 + Vite + Vant
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── LoginPage.vue   # 登录页
│   │   │   ├── HomePage.vue    # 首页工作台
│   │   │   ├── KanbanPage.vue  # 订单看板
│   │   │   ├── KanbanDetailPage.vue # 订单详情
│   │   │   ├── ScanPage.vue    # 扫码录入（购物车）
│   │   │   ├── ReceivePage.vue # 接收页
│   │   │   ├── ShipPage.vue    # 发出页
│   │   │   ├── RecordViewPage.vue # 记录详情
│   │   │   ├── NotificationPage.vue # 通知中心
│   │   │   ├── AdminUserPage.vue # 用户管理
│   │   │   ├── AdminFactoryPage.vue # 厂家管理
│   │   │   └── ExportPage.vue  # 导出页
│   │   ├── components/         # 公共组件
│   │   │   └── ProcessCard.vue # 工序卡片
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── api/                # API 调用封装
│   │   ├── router.ts           # 路由定义
│   │   └── main.ts             # 应用入口
│   └── Dockerfile
├── scripts/                    # 工具脚本
│   ├── generate_demo_data.py   # 演示数据生成
│   ├── extend_demo_data_40_plus.py # 40+ 样本扩展
│   ├── validate_main_flow.py   # 主流程验证
│   ├── human_ui_traversal.py   # H5 遍历测试
│   ├── validate_scan_cart_ui.py # 扫码购物车契约测试
│   └── validate_h5_experience_upgrade.py # H5 体验升级契约
├── docs/                       # 文档
│   ├── acceptance/             # 验收报告
│   └── 2026-06-18-全套交付文档/ # 本套文档
└── docker-compose.yml          # 容器编排
```

---

## 技术栈总览

### 后端
- 框架：FastAPI 0.100+
- ORM：SQLAlchemy 2.0
- 数据模型：Pydantic 2.0
- 数据库：MySQL 8.0
- 认证：JWT (PyJWT)
- 短信：内存模拟（演示环境）
- 容器：Docker + Python 3.11 镜像

### 前端
- 框架：Vue 3.3 + Composition API
- 构建：Vite 5.0
- UI 组件库：Vant 4.0（移动端）
- 状态管理：Pinia
- 路由：Vue Router 4
- HTTP：Axios
- 扫码：@zxing/browser
- 容器：Docker + Nginx Alpine

### 运维
- 容器编排：Docker Compose
- 日志：Docker logs + 文件日志
- 备份：MySQL 定时 dump

---

**文档结束**
