# SPEC.MD — 外协工序流转追踪系统规格说明

> 版本：v1.0  
> 日期：2026-06-16  
> 当前基线：`9cc5f7d` / `baseline-h5-scan-2026-06-16`  
> 状态：后端/API/DB 主流程通过；H5 全页面体验优化与扫码购物车式录入已完成并部署；真实手机摄像头实拍扫码未完成最终现场闭环。

---

## 1. 项目目标

建设一套用于追踪外协零件在多厂家、多工序之间实物流转的 H5 系统，实现扫码录入、接收、发出、退件、看板、通知、人员/厂家管理与数据导出。

核心目标：

1. 让每个订单、每道工序、每次流转都有记录可查。
2. 让现场操作员通过手机或扫码枪少输入、连续录入。
3. 让管理员一眼看到订单卡点、异常、逾期与待处理事项。
4. 用 API + DB + H5 体验交叉验证保证业务闭环。

---

## 2. 当前交付结论

| 维度 | 状态 | 说明 |
|---|---|---|
| 后端/API/DB 主流程 | ✅ 已通过 | 接收、分批接收、发出、下道接收、退件、DB 回查通过 |
| H5 全页面体验 | ✅ 已完成 | 登录、首页、看板、详情、接收、发出、扫码、通知、管理、导出均已优化 |
| 扫码录入 | ✅ 已完成 | 已实现“超市购物车式连续扫码” |
| Docker 部署 | ✅ 已部署 | backend/frontend/mysql 容器运行，健康检查 200 |
| 离线演示 | ✅ 已生成 | 单文件手机端离线 HTML 与 ZIP |
| 真机摄像头扫码 | ⚠️ 未最终覆盖 | 需 HTTPS + 真机权限 + 真实码样张现场验证 |

---

## 3. 用户角色

| 角色 | 主要职责 | 权限边界 |
|---|---|---|
| 企业管理员 | 全局看板、厂家/人员管理、导出、异常处理 | 全局数据 |
| 主厂家管理员 | 主厂订单协调、风险处理 | 主厂相关数据 |
| 主厂家操作员 | 扫码接收、发出、退件 | 本厂可操作记录 |
| 外协厂家管理员 | 本厂待办、异常、人员管理 | 本厂相关数据 |
| 外协厂家操作员 | 按提示完成接收/发出 | 本厂可操作记录 |

---

## 4. 核心业务流程

```text
订单/工艺路线生成
  → 每道工序生成流转记录
  → 上道工序接收
  → 上道工序发出
  → 下道工序接收
  → 如有异常则退件/通知
  → 最终完成并可导出追溯
```

扫码录入流程：

```text
进入扫码页
  → 扫码枪/手机相机/拍照/手工输入
  → 后端判断动作与可用数量
  → 加入本页清单，不跳页
  → 按行确认/修改数量/删除异常
  → 统一提交
  → 成功项标记完成，失败项保留重试
```

---

## 5. 功能规格

### 5.1 登录认证

- 手机号 + 验证码登录。
- 登录成功返回 token 与用户信息。
- 未登录访问受保护页面时跳转登录页。
- 登录页展示系统业务定位与清晰错误提示。

### 5.2 首页工作台

- 首页不是普通菜单页，而是“今日工作台”。
- 展示今日待办、逾期优先提醒、扫码录入、待接收、待发出、看板、通知、导出入口。
- 根据用户角色展示不同任务重点。

### 5.3 订单看板

- 展示订单列表、订单状态、当前卡点、流转进度。
- 支持我厂相关、待我处理、已逾期、今日更新、即将超期等筛选体验。
- 订单详情展示工序时间线、下一步建议、可接收/可发出/等待上道状态。

### 5.4 扫码录入

- 支持扫码枪连续扫码。
- 支持手机相机扫码入口。
- 支持拍照/相册识别与手工输入兜底。
- 每扫一次加入清单，不跳转页面。
- 自动判断接收/发出/查看/异常。
- 自动填入 `available_receive_qty` 或 `available_ship_qty`。
- 支持数量手输、`-`、`+`、`全部`。
- 支持重复扫码定位已有行，不新增重复行。
- 支持异常区，异常不阻断继续扫码。
- 支持统一提交、失败重试、清空已完成。

### 5.5 接收/发出/退件

- 接收数量必须大于 0 且不超过可接收数量。
- 发出数量必须大于 0 且不超过可发出数量。
- 支持分批接收、分批发出。
- 退件必须记录退件原因与数量，并影响上下道净数量。
- 操作后状态、批次、通知、日志联动。

### 5.6 通知与异常

- 通知页作为异常队列/待办中心。
- 支持单条已读、全部已读。
- 通知可跳转到对应订单或处理页面。

### 5.7 人员/厂家管理

- 企业管理员可查看、新增、审核、启用/禁用人员。
- 企业管理员可查看、新增、审核、启用/禁用厂家。
- 操作员必须绑定厂家。

### 5.8 导出

- 支持按订单、厂家、时间条件导出 Excel。
- 前端按 Blob 二进制下载，不按 JSON 解析。

---

## 6. 技术规格

| 层 | 技术 |
|---|---|
| 前端 | Vue 3、TypeScript、Vite、Vant、Pinia、Vue Router、Axios、@zxing/browser |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic、JWT、PyMySQL |
| 数据库 | MySQL 8.0、utf8mb4 |
| 部署 | Docker、Docker Compose、Nginx |
| 验证 | Python 脚本、curl、浏览器 DOM/控制台抽测 |

部署服务：

| 服务 | 端口 | 说明 |
|---|---:|---|
| MySQL | 3306 | 数据库 |
| Backend | 8000 | FastAPI API |
| Frontend | 8081 | H5 页面 |

---

## 7. API 规格

| 模块 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 认证 | POST | `/api/auth/send-sms` | 发送短信验证码 |
| 认证 | POST | `/api/auth/login` | 登录 |
| 认证 | GET | `/api/auth/me` | 当前用户 |
| 流转 | POST | `/api/records/receive` | 接收 |
| 流转 | POST | `/api/records/ship` | 发出 |
| 流转 | POST | `/api/records/return` | 退件 |
| 流转 | GET | `/api/records/{order_id}` | 订单记录列表 |
| 流转 | GET | `/api/records/scan/judge` | 扫码判断 |
| 流转 | POST | `/api/records/scan/batch` | 扫码批量提交 |
| 流转 | GET | `/api/records/detail/{record_id}` | 记录详情 |
| 看板 | GET | `/api/kanban/orders` | 订单看板 |
| 看板 | GET | `/api/kanban/orders/{order_id}/processes` | 工序看板 |
| 看板 | GET | `/api/kanban/stats` | 看板统计 |
| 通知 | GET | `/api/notifications` | 通知列表 |
| 通知 | PUT | `/api/notifications/{notification_id}/read` | 单条已读 |
| 通知 | PUT | `/api/notifications/read-all` | 全部已读 |
| 管理 | GET/POST | `/api/admin/users` | 用户列表/新增 |
| 管理 | PUT | `/api/admin/users/{user_id}/review` | 用户审核 |
| 管理 | GET/POST | `/api/admin/factories` | 厂家列表/新增 |
| 管理 | PUT | `/api/admin/factories/{factory_id}/review` | 厂家审核 |
| 导出 | GET | `/api/export/excel` | Excel 导出 |

---

## 8. 数据规格

核心表：

| 表 | 说明 |
|---|---|
| `factories` | 厂家 |
| `users` | 用户 |
| `orders` | 订单/MOM 派工单 |
| `processes` | 工艺路线 |
| `process_records` | 核心流转记录 |
| `receive_batches` | 接收批次 |
| `ship_batches` | 发出批次 |
| `return_records` | 退件记录 |
| `notifications` | 通知 |
| `action_logs` | 操作日志 |

数据要求：

- 数据库字符集使用 `utf8mb4`。
- `record_id`、`order_id`、`factory_id`、`user_id` 均按字符串处理。
- 数量变化必须可由批次表与核心记录表交叉回查。
- 不在文档中写入真实密码、token、验证码、API Key。

---

## 9. 前端体验规格

| 页面 | 体验要求 |
|---|---|
| 登录 | 系统定位清楚，错误提示人话 |
| 首页 | 今日工作台，一眼看到待办 |
| 看板 | 外协流转雷达，先看风险和卡点 |
| 详情 | 订单作战室，给下一步建议 |
| 扫码 | 连续扫码入清单，少跳转，异常后置 |
| 接收/发出 | 可操作数量突出，一键全部，超量禁止 |
| 通知 | 通知即待办，异常优先 |
| 管理 | 权限/厂家状态清晰 |
| 导出 | 快捷时间选择与导出说明 |

---

## 10. 验收规格

标准回归命令：

```bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH
cd /home/takemehome/outsourcing-track
python3 -m compileall -q backend/app scripts
python3 scripts/extend_demo_data_40_plus.py
python3 scripts/validate_main_flow.py
python3 scripts/human_ui_traversal.py
python3 scripts/validate_scan_cart_ui.py
python3 scripts/validate_h5_experience_upgrade.py
(cd frontend && npm run build)
docker compose build frontend
docker compose up -d --no-deps frontend
curl -s -o /dev/null -w 'backend=%{http_code}
' http://localhost:8000/health
curl -s -o /dev/null -w 'frontend=%{http_code}
' http://localhost:8081/
```

验收必须包含：

1. API 主流程通过。
2. DB 回查数量/状态一致。
3. H5 页面体验契约通过。
4. 浏览器控制台无 JS 错误。
5. 明确未覆盖边界。

---

## 11. 当前未覆盖边界

| 边界 | 当前状态 | 后续要求 |
|---|---|---|
| 真实手机摄像头扫码 | 未最终覆盖 | HTTPS + 真机权限 + 真实码样张 + DB 回查 |
| 外部 MOM/标准文件正式对接 | 已纳入P1 | 接真实数据源后重新做交叉验证 |
| 多浏览器兼容 | 部分覆盖 | iOS Safari、安卓微信/浏览器专项测试 |
| 生产规模性能 | 未专项压测 | 大批量订单/记录压测 |

---

## 12. 文件地图

| 类型 | 路径 |
|---|---|
| 后端 API | `backend/app/routers/` |
| 后端业务 | `backend/app/services/` |
| ORM 模型 | `backend/app/models/` |
| DDL | `backend/migrations/T2_DDL.sql` |
| 前端页面 | `frontend/src/views/` |
| 前端 API | `frontend/src/api/` |
| 前端状态 | `frontend/src/stores/` |
| 路由 | `frontend/src/router.ts` |
| 验证脚本 | `scripts/` |
| 验收报告 | `docs/acceptance/` |
| SDD 文档 | `docs/sdd/2026-06-16-current-state/` |

---

## 13. 后续优先级

| 优先级 | 任务 |
|---|---|
| P0 | 完成真实手机摄像头扫码现场闭环 |
| P1 | 接入真实 MOM/标准文件数据源 |
| P1 | 增强角色权限矩阵测试 |
| P2 | 增加 Playwright 真浏览器 E2E |
| P2 | 增加完整操作审计报表 |
| P3 | CI/CD 与生产化部署 |
