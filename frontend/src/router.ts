import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { showToast } from 'vant'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginPage.vue')
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/HomePage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/scan',
      name: 'Scan',
      component: () => import('@/views/ScanPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/receive/:record_id',
      name: 'Receive',
      component: () => import('@/views/ReceivePage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ship/:record_id',
      name: 'Ship',
      component: () => import('@/views/ShipPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/view/:record_id',
      name: 'RecordView',
      component: () => import('@/views/RecordViewPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/kanban',
      name: 'Kanban',
      component: () => import('@/views/KanbanPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/kanban/:order_id',
      name: 'KanbanDetail',
      component: () => import('@/views/KanbanDetailPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications',
      name: 'Notifications',
      component: () => import('@/views/NotificationPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/users',
      name: 'AdminUsers',
      component: () => import('@/views/AdminUserPage.vue'),
      meta: { requiresAuth: true, requiresRole: 'enterprise_admin' }
    },
    {
      path: '/admin/factories',
      name: 'AdminFactories',
      component: () => import('@/views/AdminFactoryPage.vue'),
      meta: { requiresAuth: true, requiresRole: 'enterprise_admin' }
    },
    {
      path: '/audit',
      name: 'AuditReport',
      component: () => import('@/views/AuditReportPage.vue'),
      meta: { requiresAuth: true, allowedRoles: ['enterprise_admin', 'primary_admin'] }
    },
    {
      path: '/export',
      name: 'Export',
      component: () => import('@/views/ExportPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/account',
      name: 'Account',
      component: () => import('@/views/AccountPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/password',
      name: 'Password',
      component: () => import('@/views/PasswordPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/permissions',
      name: 'Permissions',
      component: () => import('@/views/PermissionsPage.vue'),
      meta: { requiresAuth: true, allowedRoles: ['super_admin', 'factory_admin'] }
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  authStore.initFromStorage()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    showToast('请先登录')
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else if (to.meta.requiresRole) {
    // 检查角色权限
    const userRole = authStore.userInfo?.role
    if (userRole !== to.meta.requiresRole) {
      showToast('无权限访问')
      next('/')
    } else {
      next()
    }
  } else if (to.meta.allowedRoles) {
    const userRole = authStore.userInfo?.role
    const allowedRoles = to.meta.allowedRoles as string[]
    if (!userRole || !allowedRoles.includes(userRole)) {
      showToast('无权限访问')
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
