# 人类用户 UI 遍历测试报告
生成时间：2026-06-17T22:40:26
测试模式：api-assisted-mobile-ui-traversal
说明：当前环境未装浏览器；Playwright 浏览器下载超时，因此本轮为 API+源码契约辅助的人类UI遍历，不是像素级真实点击。

## 总结

- 总检查项：66
- 通过：66
- 未通过/待修复：0
- 未通过分布：{}

## 未通过项

## 全量检查明细
1. ✅ `/` / 页面入口 / 移动端访问 SPA shell
2. ✅ `/login` / 页面入口 / 移动端访问 SPA shell
3. ✅ `/scan` / 页面入口 / 移动端访问 SPA shell
4. ✅ `/kanban` / 页面入口 / 移动端访问 SPA shell
5. ✅ `/notifications` / 页面入口 / 移动端访问 SPA shell
6. ✅ `/export` / 页面入口 / 移动端访问 SPA shell
7. ✅ `/admin/users` / 页面入口 / 移动端访问 SPA shell
8. ✅ `/admin/factories` / 页面入口 / 移动端访问 SPA shell
9. ✅ `/login` / 手机号输入框/发送验证码 / 输入非法手机号 123
10. ✅ `/login` / 验证码输入框/登录按钮 / 输入错误验证码
11. ✅ `/login` / 登录按钮 / enterprise 使用验证码登录
12. ✅ `/login` / 登录后用户信息 / enterprise 获取当前用户
13. ✅ `/login` / 登录按钮 / primary_admin 使用验证码登录
14. ✅ `/login` / 登录后用户信息 / primary_admin 获取当前用户
15. ✅ `/login` / 登录按钮 / a_operator 使用验证码登录
16. ✅ `/login` / 登录后用户信息 / a_operator 获取当前用户
17. ✅ `/login` / 登录按钮 / b_operator 使用验证码登录
18. ✅ `/login` / 登录后用户信息 / b_operator 获取当前用户
19. ✅ `/` / 我的通知入口/未读数 / 加载通知列表
20. ✅ `/` / 看板快捷入口 / 加载看板订单
21. ✅ `/kanban` / 顶部统计卡片 / 请求统计数据
22. ✅ `/kanban` / 顶部统计卡片 / 页面装载后自动显示统计
23. ✅ `/kanban` / Tab 全部 / 切换筛选并加载订单
24. ✅ `/kanban` / Tab pending / 切换筛选并加载订单
25. ✅ `/kanban` / Tab in_progress / 切换筛选并加载订单
26. ✅ `/kanban` / Tab completed / 切换筛选并加载订单
27. ✅ `/kanban/:order_id` / 订单卡片 / 点击 DEMO_PENDING_001 进入工序详情
28. ✅ `/kanban/:order_id` / 订单卡片 / 点击 DEMO_RECEIVED_001 进入工序详情
29. ✅ `/kanban/:order_id` / 订单卡片 / 点击 DEMO_SPLIT_001 进入工序详情
30. ✅ `/kanban/:order_id` / 订单卡片 / 点击 DEMO_OVERDUE_001 进入工序详情
31. ✅ `/kanban/:order_id` / 订单卡片 / 点击 DEMO_DONE_001 进入工序详情
32. ✅ `/kanban/:order_id` / 厂家角色工序可见范围 / B厂用户查看 DEMO_SPLIT_001 工序详情
33. ✅ `/view/:record_id` / 跨厂详情权限 / B厂用户直接打开A厂记录 DEMO_RECEIVED_R1
34. ✅ `/scan` / 手动输入解析按钮 / 输入 record_DEMO_PENDING_R1
35. ✅ `/scan` / 手动输入解析按钮 / 输入 record_DEMO_RECEIVED_R1
36. ✅ `/scan` / 手动输入解析按钮 / 输入 record_DEMO_SPLIT_R1
37. ✅ `/scan` / 手动输入解析按钮 / 输入 record_DEMO_OVERDUE_R1
38. ✅ `/scan` / 手动输入解析按钮 / 输入 record_DEMO_DONE_R1
39. ✅ `/scan` / 手动输入解析按钮 / 输入 bad_qr
40. ✅ `/scan` / 相机扫码Tab / 打开相机扫码
41. ✅ `/receive/:record_id` / 页面加载 / 打开待接收记录
42. ✅ `/receive/:record_id` / 接收数量输入框 / 输入0提交
43. ✅ `/receive/:record_id` / 接收数量输入框 / 输入负数提交
44. ✅ `/receive/:record_id` / 提交按钮权限 / B厂用户接收A厂记录
45. ✅ `/ship/:record_id` / 页面加载 / 打开已接收待发出记录
46. ✅ `/ship/:record_id` / 发出数量输入框 / 输入0提交
47. ✅ `/ship/:record_id` / 发出数量输入框 / 输入超过已接收数量提交
48. ✅ `/ship/:record_id` / 提交按钮权限 / B厂用户发出A厂记录
49. ✅ `/ship/:record_id` / 退件弹窗确认按钮 / 后端退件接口可用性
50. ✅ `/ship/:record_id` / 退件弹窗确认按钮 / 前端点击退件确认
51. ✅ `/view/:record_id` / 刷新/批次列表 / 打开 DEMO_SPLIT_R1 查看批次
52. ✅ `/view/:record_id` / 刷新/批次列表 / 打开 DEMO_OVERDUE_R1 查看批次
53. ✅ `/view/:record_id` / 刷新/批次列表 / 打开 DEMO_DONE_R1 查看批次
54. ✅ `/view/:record_id` / 锁定状态/操作按钮 / 根据 lock_type 显示按钮
55. ✅ `/notifications` / 通知列表 / 加载A厂用户通知
56. ✅ `/notifications` / 通知项点击 / 点击未读通知标记已读
57. ✅ `/notifications` / 全部已读 / 后端批量已读接口
58. ✅ `/notifications` / 全部已读 / 前端点击全部已读
59. ✅ `/export` / 导出Excel按钮 / 选择日期后导出
60. ✅ `/export` / 厂家选择字段 / 加载厂家选择列表
61. ✅ `/export` / 订单号输入框 / 输入订单号过滤导出
62. ✅ `/export` / 下载文件处理 / 前端保存 Blob
63. ✅ `/admin/users` / 人员管理列表 / 企业管理员打开人员管理
64. ✅ `/admin/users` / 添加用户/审核按钮 / 提交添加和审核
65. ✅ `/admin/factories` / 厂家管理列表 / 企业管理员打开厂家管理
66. ✅ `/admin/*` / 路由权限守卫 / 非企业管理员访问管理页
