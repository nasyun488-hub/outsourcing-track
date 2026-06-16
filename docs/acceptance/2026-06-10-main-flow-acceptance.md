# 验收卡：外协工序主流程闭环

日期：2026-06-10
方法论：MADM-Solo Phase 4 风险驱动验证

## 当前价值切片
P0 主流程闭环：登录 → 看板 → 接收 → 分批接收 → 发出 → 下道接收 → 退件/查看 → DB核对

## 主流程验证
- [ ] 登录获取 token
- [ ] 看板订单接口返回 200
- [ ] 首道工序首次接收成功，DB 写入 receive_qty，状态变更
- [ ] 同一工序分批接收不被 entry_lock 阻断
- [ ] 工序发出逻辑可执行或明确阻断原因符合业务规则
- [ ] 下道工序接收后，上道锁状态正确变化
- [ ] 订单状态与工序状态联动

## 自动测试
- [ ] backend pytest 通过
- [ ] frontend build 通过
- [ ] docker compose 服务健康

## 数据验证
- [ ] API 返回与 DB 一致
- [ ] total_receive_qty / total_ship_qty 正确累加
- [ ] lock_type 无死锁
- [ ] 异常输入不污染数据

## 发布检查
- [ ] Backend health 200
- [ ] Frontend 200
- [ ] 日志无启动错误
- [ ] 当前改动可追踪

## 结论
待执行脚本实测。
