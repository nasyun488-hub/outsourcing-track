<template>
  <div class="permissions-page">
    <!-- 顶部导航 -->
    <nav class="top-nav">
      <div class="nav-left">
        <button class="back-btn" @click="goBack">
          <i class="icon">←</i>
        </button>
        <h1 class="page-title">权限管理</h1>
      </div>
    </nav>

    <div class="content">
      <!-- 当前权限卡片 -->
      <div class="current-permission">
        <div class="permission-header">
          <div class="permission-icon">🔑</div>
          <div class="permission-info">
            <div class="permission-title">当前角色</div>
            <div class="permission-role">{{ roleText }}</div>
          </div>
        </div>
        <div class="permission-desc">
          您的账号拥有 {{ roleText }} 权限级别
        </div>
      </div>

      <!-- 角色权限列表 -->
      <div class="role-list">
        <div class="list-title">角色权限说明</div>
        
        <div class="role-card" v-for="role in roleList" :key="role.id">
          <div class="role-header">
            <div class="role-name">{{ role.name }}</div>
            <div class="role-badge" :class="'level-' + role.level">
              级别 {{ role.level }}
            </div>
          </div>
          
          <div class="permission-items">
            <div 
              class="permission-item" 
              v-for="perm in role.permissions" 
              :key="perm"
            >
              <span class="check-icon">✓</span>
              <span class="perm-text">{{ perm }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作提示 -->
      <div class="tip-section">
        <p class="tip-text">
          如需调整用户权限，请联系超级管理员
        </p>
        <p class="tip-subtext">
          客服电话：400-xxx-xxxx
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const currentUser = computed(() => authStore.user)

const roleText = computed(() => {
  const roleMap: Record<string, string> = {
    // 规范角色（与后端 user_role_enum 一致）
    'enterprise_admin': '企业管理员',
    'primary_admin': '主厂管理员',
    'primary_operator': '主厂操作员',
    'cooperative_admin': '协作厂管理员',
    'cooperative_operator': '协作厂操作员',
    // 历史别名兜底
    'super_admin': '企业管理员',
    'factory_admin': '协作厂管理员',
    'factory_operator': '协作厂操作员',
    'operator': '协作厂操作员',
    'factory_staff': '主厂操作员',
    'external_factory': '协作厂管理员',
    'guest': '访客'
  }
  return roleMap[currentUser.value?.role] || currentUser.value?.role || ''
})

const roleList = [
  {
    id: 'enterprise_admin',
    name: '企业管理员',
    level: 5,
    permissions: [
      '管理所有用户账号',
      '管理所有厂家信息',
      '查看所有流转记录（可跨厂）',
      '导出全部数据',
      '系统日志审计',
      'MOM 订单导入'
    ]
  },
  {
    id: 'primary_admin',
    name: '主厂管理员',
    level: 4,
    permissions: [
      '查看本厂流转记录',
      '本厂数据导出',
      '审计日志查看',
      '看板与订单跟踪'
    ]
  },
  {
    id: 'primary_operator',
    name: '主厂操作员',
    level: 3,
    permissions: [
      '扫码接收/发出',
      '查看本厂流转记录',
      '查看记录详情与批次',
      '退件与解锁申请'
    ]
  },
  {
    id: 'cooperative_admin',
    name: '协作厂管理员',
    level: 2,
    permissions: [
      '本厂扫码接收/发出',
      '查看本厂待处理订单',
      '本厂数据导出'
    ]
  },
  {
    id: 'cooperative_operator',
    name: '协作厂操作员',
    level: 1,
    permissions: [
      '扫码接收确认',
      '扫码发出',
      '查看本厂流转记录'
    ]
  }
]

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.permissions-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #ffffff;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e5e5;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn:hover {
  background: #f0f0f0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.content {
  padding: 16px;
  padding-bottom: 40px;
}

.current-permission {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  color: white;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.permission-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.permission-icon {
  font-size: 36px;
}

.permission-title {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.permission-role {
  font-size: 20px;
  font-weight: 600;
}

.permission-desc {
  font-size: 13px;
  opacity: 0.85;
}

.role-list {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.role-card {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
}

.role-card:last-child {
  margin-bottom: 0;
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.role-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.role-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.level-5 {
  background: #9b59b6;
}

.level-4 {
  background: #3498db;
}

.level-3 {
  background: #27ae60;
}

.level-2 {
  background: #f39c12;
}

.level-1 {
  background: #95a5a6;
}

.permission-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.check-icon {
  color: #27ae60;
  font-size: 14px;
}

.tip-section {
  background: #fff9e6;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.tip-text {
  font-size: 14px;
  color: #92400e;
  margin: 0 0 4px 0;
}

.tip-subtext {
  font-size: 13px;
  color: #b45309;
  margin: 0;
}
</style>
