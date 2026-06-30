<template>
  <div id="app" :class="{ 'bottom-nav-hidden': isLoginPage }">
    <!-- 全局加载指示器 -->
    <div v-if="loadingStore.isLoading" class="global-loading-mask" />
    <div v-if="loadingStore.isLoading" class="global-loading">
      <div class="loading-spinner"></div>
      <div style="margin-top: 8px; font-size: 14px;">{{ loadingStore.loadingText }}</div>
    </div>

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
            <van-dropdown>
              <van-dropdown-item>
                <template #title>
                  <button class="topbar-user">{{ authStore.userInfo?.name || '用户' }}</button>
                </template>
                <van-cell-group>
                  <van-cell title="系统设置" is-link @click="router.push('/settings')" />
                  <van-cell title="退出登录" is-link @click="confirmLogout" />
                </van-cell-group>
              </van-dropdown-item>
            </van-dropdown>
          </div>
        </header>

        <main class="main-content">
          <router-view />
        </main>
      </section>
    </div>

    <!-- 移动端底部导航栏 -->
    <nav class="bottom-nav">
      <button
        v-for="item in mobileNavItems"
        :key="item.path"
        class="bottom-nav-item"
        :class="{ active: isActive(item.path) }"
        @click="router.push(item.path)"
      >
        <span class="bottom-nav-icon">{{ item.icon }}</span>
        <span class="bottom-nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 900 : false)

// 路由跳转时显示loading
router.beforeEach((to, from, next) => {
  if (to.path !== from.path) {
    loadingStore.showLoading('加载中...')
  }
  next()
})

router.afterEach(() => {
  // 延迟隐藏，避免闪烁
  setTimeout(() => {
    loadingStore.hideLoading()
  }, 300)
})

onMounted(() => {
  const checkMobile = () => {
    isMobile.value = window.innerWidth < 900
  }
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

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
  { path: '/settings', label: '设置中心', icon: '⚙️' },
  { path: '/admin/users', label: '人员管理', icon: '👥', roles: ['enterprise_admin'] },
  { path: '/admin/factories', label: '厂家管理', icon: '🏭', roles: ['enterprise_admin'] }
]

const mobileNavItems = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/scan', label: '扫码', icon: '📷' },
  { path: '/notifications', label: '通知', icon: '🔔' },
  { path: '/settings', label: '设置', icon: '⚙️' }
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

function confirmLogout() {
  if (confirm('确定要退出登录吗？')) {
    authStore.logout()
  }
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
    padding-bottom: 70px;
  }
}

/* 移动端底部导航栏 */
.bottom-nav {
  display: none;
}

/* 登录页隐藏底部导航 */
body:has(.van-tabbar--fixed) .bottom-nav,
.login-page + .bottom-nav,
#app:has(.login-page) .bottom-nav {
  display: none !important;
}

@media (max-width: 900px) {
  .bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    min-height: 56px;
    display: flex !important;
    align-items: center;
    justify-content: space-around;
    background: #fff;
    border-top: 1px solid #e5e7eb;
    z-index: 9999;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }

  /* 登录页不显示底部导航 */
  .bottom-nav-hidden .bottom-nav {
    display: none !important;
  }

  .bottom-nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 0;
    border: none;
    background: transparent;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
  }

  .bottom-nav-item.active {
    color: #2f6bff;
  }

  .bottom-nav-icon {
    font-size: 20px;
  }

  .bottom-nav-label {
    font-size: 11px;
    font-weight: 500;
  }
}
</style>
