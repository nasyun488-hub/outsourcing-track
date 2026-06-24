<template>
  <div id="app">
    <router-view v-if="isLoginPage" />

    <div v-else class="pc-shell">
      <aside class="side-nav">
        <div class="brand-block" @click="router.push('/')">
          <div class="brand-logo">协</div>
          <div>
            <div class="brand-title">外协流转</div>
            <div class="brand-subtitle">PC工作台</div>
          </div>
        </div>

        <nav class="nav-list">
          <button
            v-for="item in visibleNavItems"
            :key="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            @click="router.push(item.path)"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </button>
        </nav>
      </aside>

      <section class="pc-main">
        <header class="topbar">
          <div>
            <div class="topbar-title">{{ currentTitle }}</div>
            <div class="topbar-subtitle">{{ roleText }} · {{ authStore.userInfo?.factory_name || '全部厂家' }}</div>
          </div>
          <div class="topbar-actions">
            <button class="topbar-btn" @click="router.push('/notifications')">通知</button>
            <button class="topbar-btn primary" @click="router.push('/scan')">扫码录入</button>
            <button class="topbar-user" @click="authStore.logout()">{{ authStore.userInfo?.name || '用户' }}</button>
          </div>
        </header>

        <main class="main-content">
          <router-view />
        </main>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')

const roleMap: Record<string, string> = {
  enterprise_admin: '企业管理员',
  primary_admin: '主厂管理员',
  primary_operator: '主厂操作员',
  cooperative_admin: '协作厂管理员',
  cooperative_operator: '协作厂操作员',
  factory_admin: '厂家管理员',
  factory_operator: '厂家操作员',
  operator: '操作员',
  admin: '管理员'
}

const roleText = computed(() => {
  const role = authStore.userInfo?.role
  return role ? roleMap[role] || role : '未登录'
})

const navItems = [
  { path: '/', label: '今日工作台', icon: '🏠' },
  { path: '/kanban', label: '企业看板', icon: '📊' },
  { path: '/scan', label: '扫码录入', icon: '📷' },
  { path: '/notifications', label: '通知待办', icon: '🔔' },
  { path: '/audit', label: '审计报表', icon: '🧾', roles: ['enterprise_admin', 'primary_admin'] },
  { path: '/export', label: '数据导出', icon: '📤' },
  { path: '/admin/users', label: '人员管理', icon: '👥', roles: ['enterprise_admin'] },
  { path: '/admin/factories', label: '厂家管理', icon: '🏭', roles: ['enterprise_admin'] }
]

const visibleNavItems = computed(() => {
  const role = authStore.userInfo?.role
  return navItems.filter(item => !item.roles || (role && item.roles.includes(role)))
})

const currentTitle = computed(() => {
  const matched = navItems
    .filter(item => route.path === item.path || (item.path !== '/' && route.path.startsWith(item.path)))
    .sort((a, b) => b.path.length - a.path.length)[0]
  if (route.path.startsWith('/kanban/')) return '订单工序详情'
  if (route.path.startsWith('/receive/')) return '接收登记'
  if (route.path.startsWith('/ship/')) return '发出登记'
  if (route.path.startsWith('/view/')) return '流转记录'
  return matched?.label || '外协流转'
})

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style>
html,
body,
#app {
  width: 100%;
  min-height: 100%;
  margin: 0;
}

#app {
  width: 100%;
  height: 100%;
  background: #eef3fb;
}

* {
  box-sizing: border-box;
}

.pc-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  background: #eef3fb;
}

.side-nav {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 18px 14px;
  color: #fff;
  background: linear-gradient(180deg, #13233f 0%, #0d1730 100%);
  box-shadow: 8px 0 28px rgba(15, 35, 70, 0.14);
  z-index: 10;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px 22px;
  cursor: pointer;
}

.brand-logo {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-weight: 900;
  background: linear-gradient(135deg, #2f6bff, #7d63ff);
  box-shadow: 0 10px 22px rgba(47, 107, 255, 0.3);
}

.brand-title {
  font-size: 17px;
  font-weight: 900;
}

.brand-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #93a4c5;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 13px;
  border: 0;
  border-radius: 13px;
  color: #c6d2ec;
  background: transparent;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.nav-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-item.active {
  color: #fff;
  background: linear-gradient(135deg, #2f6bff, #655bff);
  box-shadow: 0 12px 22px rgba(47, 107, 255, 0.24);
}

.nav-icon {
  width: 20px;
  text-align: center;
}

.pc-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 8;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid #e3e9f5;
  backdrop-filter: blur(12px);
}

.topbar-title {
  font-size: 20px;
  font-weight: 900;
  color: #18243a;
}

.topbar-subtitle {
  margin-top: 3px;
  font-size: 12px;
  color: #75829a;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-btn,
.topbar-user {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #d8e1f0;
  border-radius: 999px;
  color: #35435f;
  background: #fff;
  cursor: pointer;
}

.topbar-btn.primary {
  border-color: #2f6bff;
  color: #fff;
  background: #2f6bff;
}

.topbar-user {
  font-weight: 700;
}

.main-content {
  width: 100%;
  max-width: 1360px;
  padding: 22px 24px 36px;
}

@media (max-width: 900px) {
  .pc-shell {
    display: block;
  }

  .side-nav,
  .topbar {
    display: none;
  }

  .main-content {
    max-width: none;
    padding: 0;
  }
}
</style>
