-- ============================================================
-- 外协工序流转追踪系统 — MySQL 8.0 DDL
-- 版本：v1.0  日期：2026-05-22
-- 编码：utf8mb4  排序规则：utf8mb4_unicode_ci
-- ============================================================

CREATE DATABASE IF NOT EXISTS outsourcing_track
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE outsourcing_track;

-- ----------------------------------------------------------
-- 1. factories 厂家表
-- ----------------------------------------------------------
CREATE TABLE factories (
    factory_id    VARCHAR(64)  NOT NULL COMMENT '厂家ID（雪花算法或UUID）',
    factory_name  VARCHAR(128) NOT NULL COMMENT '厂家名称',
    factory_type  ENUM('primary','cooperative') NOT NULL DEFAULT 'cooperative' COMMENT 'primary=主厂家，cooperative=配合工序厂家',
    factory_phone VARCHAR(20)  DEFAULT NULL COMMENT '联系电话',
    factory_address VARCHAR(256) DEFAULT NULL COMMENT '地址',
    status        ENUM('active','inactive','pending') NOT NULL DEFAULT 'pending' COMMENT 'active/待审核/inactive',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (factory_id),
    UNIQUE KEY uk_factory_name (factory_name)
) ENGINE=InnoDB COMMENT='厂家表';

-- ----------------------------------------------------------
-- 2. users 用户表
-- ----------------------------------------------------------
CREATE TABLE users (
    user_id       VARCHAR(64)  NOT NULL COMMENT '用户ID',
    factory_id    VARCHAR(64)  NOT NULL COMMENT '所属厂家ID',
    phone         VARCHAR(20)  NOT NULL COMMENT '手机号（登录账号）',
    name          VARCHAR(32)  NOT NULL COMMENT '姓名',
    role          ENUM('enterprise_admin','primary_admin','primary_operator','cooperative_admin','cooperative_operator') NOT NULL COMMENT '5种角色',
    password_hash VARCHAR(256)  NOT NULL COMMENT '密码哈希（JWT场景下可不用，但预留）',
    status        ENUM('active','inactive','pending') NOT NULL DEFAULT 'pending' COMMENT 'pending=待审核',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_phone (phone),
    KEY idx_factory_id (factory_id),
    CONSTRAINT fk_users_factory FOREIGN KEY (factory_id) REFERENCES factories(factory_id)
) ENGINE=InnoDB COMMENT='用户表';

-- ----------------------------------------------------------
-- 3. orders 订单表（MOM 派工单）
-- ----------------------------------------------------------
CREATE TABLE orders (
    order_id           VARCHAR(64)  NOT NULL COMMENT '订单号（MOM派工单号）',
    primary_factory_id VARCHAR(64) NOT NULL COMMENT '主厂家ID',
    order_status       ENUM('pending','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',
    total_qty          INT          NOT NULL DEFAULT 0 COMMENT '订单总数量',
    mom_created_at     DATETIME     DEFAULT NULL COMMENT 'MOM系统创建时间',
    created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id),
    KEY idx_primary_factory (primary_factory_id),
    CONSTRAINT fk_orders_factory FOREIGN KEY (primary_factory_id) REFERENCES factories(factory_id)
) ENGINE=InnoDB COMMENT='订单表';

-- ----------------------------------------------------------
-- 4. processes 工序表（每订单一条工艺路线）
-- ----------------------------------------------------------
CREATE TABLE processes (
    process_id    VARCHAR(64)  NOT NULL COMMENT '工序ID',
    order_id      VARCHAR(64)  NOT NULL COMMENT '所属订单ID',
    process_seq   VARCHAR(16)  NOT NULL COMMENT '工序编码（如010/020），保留前导零',
    process_name  VARCHAR(64)  NOT NULL COMMENT '工序名称',
    factory_id    VARCHAR(64)  NOT NULL COMMENT '承接厂家ID',
    process_order INT          NOT NULL COMMENT '工序顺序号（1,2,3...）',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (process_id),
    UNIQUE KEY uk_order_seq (order_id, process_seq),
    KEY idx_order_id (order_id),
    KEY idx_factory_id (factory_id),
    CONSTRAINT fk_processes_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_processes_factory FOREIGN KEY (factory_id) REFERENCES factories(factory_id)
) ENGINE=InnoDB COMMENT='工序表';

-- ----------------------------------------------------------
-- 5. process_records 流转记录表（核心表）
-- ----------------------------------------------------------
CREATE TABLE process_records (
    record_id           VARCHAR(64)  NOT NULL COMMENT '记录ID',
    order_id            VARCHAR(64)  NOT NULL COMMENT '订单ID',
    process_id          VARCHAR(64)  NOT NULL COMMENT '工序ID',
    factory_id          VARCHAR(64)  NOT NULL COMMENT '承接厂家ID',
    record_status       ENUM('pending','received','shipped','completed') NOT NULL DEFAULT 'pending' COMMENT '流转阶段',
    lock_type           ENUM('none','entry_lock','relation_lock','sync_lock') NOT NULL DEFAULT 'none' COMMENT '锁定类型',
    total_receive_qty   INT          NOT NULL DEFAULT 0 COMMENT '累计接收数量',
    total_ship_qty      INT          NOT NULL DEFAULT 0 COMMENT '累计发出数量',
    partial_receive     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否部分接收（0=否，1=是）',
    partial_ship       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否部分发出（0=否，1=是）',
    last_receive_time   DATETIME     DEFAULT NULL COMMENT '最后接收时间',
    last_ship_time      DATETIME     DEFAULT NULL COMMENT '最后发出时间',
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (record_id),
    UNIQUE KEY uk_order_process (order_id, process_id),
    KEY idx_order_id (order_id),
    KEY idx_factory_id (factory_id),
    KEY idx_record_status (record_status),
    CONSTRAINT fk_records_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_records_process FOREIGN KEY (process_id) REFERENCES processes(process_id),
    CONSTRAINT fk_records_factory FOREIGN KEY (factory_id) REFERENCES factories(factory_id)
) ENGINE=InnoDB COMMENT='流转记录表（核心）';

-- ----------------------------------------------------------
-- 6. receive_batches 接收批次表
-- ----------------------------------------------------------
CREATE TABLE receive_batches (
    batch_id      VARCHAR(64)  NOT NULL COMMENT '批次ID',
    record_id     VARCHAR(64)  NOT NULL COMMENT '所属流转记录ID',
    user_id       VARCHAR(64)  NOT NULL COMMENT '接收人ID',
    receive_time  DATETIME     NOT NULL COMMENT '接收时间',
    receive_qty   INT          NOT NULL COMMENT '接收数量',
    batch_no      INT          NOT NULL COMMENT '批次序号（同一record的第N次接收）',
    return_qty    INT          NOT NULL DEFAULT 0 COMMENT '累计退件数量（负数计入）',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (batch_id),
    KEY idx_record_id (record_id),
    KEY idx_user_id (user_id),
    CONSTRAINT fk_receive_record FOREIGN KEY (record_id) REFERENCES process_records(record_id),
    CONSTRAINT fk_receive_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='接收批次表';

-- ----------------------------------------------------------
-- 7. ship_batches 发出批次表
-- ----------------------------------------------------------
CREATE TABLE ship_batches (
    batch_id      VARCHAR(64)  NOT NULL COMMENT '批次ID',
    record_id     VARCHAR(64)  NOT NULL COMMENT '所属流转记录ID',
    user_id       VARCHAR(64)  NOT NULL COMMENT '发出人ID',
    ship_time     DATETIME     NOT NULL COMMENT '发出时间',
    ship_qty      INT          NOT NULL COMMENT '发出数量',
    batch_no      INT          NOT NULL COMMENT '批次序号',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (batch_id),
    KEY idx_record_id (record_id),
    KEY idx_user_id (user_id),
    CONSTRAINT fk_ship_record FOREIGN KEY (record_id) REFERENCES process_records(record_id),
    CONSTRAINT fk_ship_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='发出批次表';

-- ----------------------------------------------------------
-- 8. return_records 退件记录表
-- ----------------------------------------------------------
CREATE TABLE return_records (
    return_id      VARCHAR(64)  NOT NULL COMMENT '退件ID',
    from_record_id VARCHAR(64)  NOT NULL COMMENT '退出发送方流转记录ID',
    to_record_id   VARCHAR(64)  NOT NULL COMMENT '接收退回方流转记录ID',
    user_id        VARCHAR(64)  NOT NULL COMMENT '操作人ID',
    return_reason  VARCHAR(256) NOT NULL COMMENT '退件原因',
    return_qty     INT          NOT NULL COMMENT '退件数量（正数）',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (return_id),
    KEY idx_from_record (from_record_id),
    KEY idx_to_record (to_record_id),
    KEY idx_user_id (user_id),
    CONSTRAINT fk_return_from FOREIGN KEY (from_record_id) REFERENCES process_records(record_id),
    CONSTRAINT fk_return_to FOREIGN KEY (to_record_id) REFERENCES process_records(record_id),
    CONSTRAINT fk_return_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='退件记录表';

-- ----------------------------------------------------------
-- 9. notifications 应用内通知表
-- ----------------------------------------------------------
CREATE TABLE notifications (
    notif_id    VARCHAR(64)  NOT NULL COMMENT '通知ID',
    user_id     VARCHAR(64)  NOT NULL COMMENT '通知用户ID',
    title       VARCHAR(128) NOT NULL COMMENT '通知标题',
    content     TEXT         NOT NULL COMMENT '通知内容',
    notif_type  ENUM('transfer','sync_error','approval','register','other') NOT NULL DEFAULT 'other' COMMENT '通知类型',
    is_read     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否已读',
    related_id  VARCHAR(64)  DEFAULT NULL COMMENT '关联业务ID（如record_id）',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notif_id),
    KEY idx_user_id (user_id),
    KEY idx_is_read (is_read),
    KEY idx_created_at (created_at),
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='应用内通知表';

-- ----------------------------------------------------------
-- 10. approval_requests 修改审批表
-- ----------------------------------------------------------
CREATE TABLE approval_requests (
    request_id   VARCHAR(64)  NOT NULL COMMENT '审批ID',
    record_id    VARCHAR(64)  NOT NULL COMMENT '关联流转记录ID',
    requester_id VARCHAR(64)  NOT NULL COMMENT '申请人ID',
    approver_id  VARCHAR(64)  DEFAULT NULL COMMENT '审批人ID',
    status       ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending' COMMENT '审批状态',
    request_type ENUM('unlock','modify','cancel') NOT NULL COMMENT '申请类型',
    content      TEXT         NOT NULL COMMENT '申请说明/修改内容',
    old_values   JSON         DEFAULT NULL COMMENT '修改前值',
    new_values   JSON         DEFAULT NULL COMMENT '修改后值',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at  DATETIME     DEFAULT NULL COMMENT '审批时间',
    PRIMARY KEY (request_id),
    KEY idx_record_id (record_id),
    KEY idx_requester (requester_id),
    KEY idx_approver (approver_id),
    KEY idx_status (status),
    CONSTRAINT fk_approval_record FOREIGN KEY (record_id) REFERENCES process_records(record_id),
    CONSTRAINT fk_approval_requester FOREIGN KEY (requester_id) REFERENCES users(user_id),
    CONSTRAINT fk_approval_approver FOREIGN KEY (approver_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='修改审批表';

-- ----------------------------------------------------------
-- 11. action_logs 操作日志表
-- ----------------------------------------------------------
CREATE TABLE action_logs (
    log_id        VARCHAR(64)  NOT NULL COMMENT '日志ID',
    user_id       VARCHAR(64)  NOT NULL COMMENT '操作用户ID',
    action_type   VARCHAR(32)  NOT NULL COMMENT '操作类型（如RECEIVE,SHIP,RETURN,UNLOCK等）',
    target_table  VARCHAR(32)  NOT NULL COMMENT '操作表名',
    target_id     VARCHAR(64)  NOT NULL COMMENT '操作记录ID',
    old_value     JSON         DEFAULT NULL COMMENT '修改前值',
    new_value     JSON         DEFAULT NULL COMMENT '修改后值',
    ip_address    VARCHAR(45)  DEFAULT NULL COMMENT 'IP地址',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    KEY idx_user_id (user_id),
    KEY idx_action_type (action_type),
    KEY idx_target (target_table, target_id),
    KEY idx_created_at (created_at),
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB COMMENT='操作日志表';

-- ----------------------------------------------------------
-- 12. sms_codes 短信验证码表（登录用）
-- ----------------------------------------------------------
CREATE TABLE sms_codes (
    id          BIGINT        NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    phone       VARCHAR(20)   NOT NULL COMMENT '手机号',
    code        VARCHAR(8)   NOT NULL COMMENT '验证码',
    expires_at  DATETIME     NOT NULL COMMENT '过期时间',
    used        TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否已使用',
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_phone_code (phone, code, used),
    KEY idx_expires_at (expires_at)
) ENGINE=InnoDB COMMENT='短信验证码表';
