<template>
  <div class="home-page">
    <div class="hero-card">
      <div class="hero-top">
        <div class="avatar-wrap">
          <van-icon name="user-o" size="30" color="#2f6bff" />
        </div>
        <div class="user-details">
          <div class="hello">{{ greeting }}，{{ userInfo?.name || '外协伙伴' }}</div>
          <div class="role-line">
            <span class="role-pill">{{ roleText }}</span>
            <span class="factory-name">{{ userInfo?.factory_name || '全部厂家' }}</span>
          </div>
        </div>
        <van-badge :content="unreadCount" :show-zero="false" max="99">
          <van-icon name="bell" size="24" color="#fff" @click="goToNotifications" />
        </van-badge>
      </div>

      <div class="workbench-title">今日工作台</div>
      <div class="workbench-subtitle">按现场一天工作节奏：先看逾期，再扫码录入，最后复核通知。</div>

      <div class="overview-card">
        <div class="overview-header">
          <div>
            <div class="overview-title">今日待办</div>
            <div class="overview-subtitle">把需要人处理的事放在最前面</div>
          </div>
          <van-tag v-if="stats.overdue_count" type="danger" round>逾期优先</van-tag>
        </div>
        <div class="overview-grid">
          <div class="overview-item">
            <div class="overview-num pending">{{ stats.pending }}</div>
            <div class="overview-label">待处理</div>
          </div>
          <div class="overview-item">
            <div class="overview-num processing">{{ stats.in_progress }}</div>
            <div class="overview-label">进行中</div>
          </div>
          <div class="overview-item">
            <div class="overview-num overdue">{{ stats.overdue_count }}</div>
            <div class="overview-label">已逾期</div>
          </div>
          <div class="overview-item">
            <div class="overview-num completed">{{ stats.completed }}</div>
            <div class="overview-label">已完成</div>
          </div>
        </div>
        <div v-if="stats.overdue_count" class="overview-alert" @click="goToOverdue">
          <van-icon name="warning-o" /> 有 {{ stats.overdue_count }} 道逾期工序，请优先处理
        </div>
        <div v-else class="overview-ok">
          <van-icon name="passed" /> 暂无逾期工序，按计划推进即可
        </div>
      </div>
    </div>

    <div class="section-block rhythm-block">
      <div class="section-header">
        <div>
          <div class="section-title">现场节奏</div>
          <div class="section-subtitle">少点菜单，多按任务顺序行动</div>
        </div>
      </div>
      <div class="rhythm-list">
        <div class="rhythm-item urgent" @click="goToOverdue">
          <span class="step">1</span>
          <div class="rhythm-content">
            <div class="rhythm-title">逾期优先处理</div>
            <div class="rhythm-desc">先定位卡住的工序，避免流转继续延误</div>
          </div>
          <van-icon name="arrow" />
        </div>
        <div class="rhythm-item" @click="goToScan">
          <span class="step">2</span>
          <div class="rhythm-content">
            <div class="rhythm-title">开始扫码录入</div>
            <div class="rhythm-desc">扫码后按订单状态接收或发出，无需手输订单号</div>
          </div>
          <van-icon name="arrow" />
        </div>
        <div class="rhythm-item" @click="goToKanban">
          <span class="step">3</span>
          <div class="rhythm-content">
            <div class="rhythm-title">复核流转进度</div>
            <div class="rhythm-desc">查看待接收、待发出和异常提醒是否清零</div>
          </div>
          <van-icon name="arrow" />
        </div>
      </div>
    </div>

    <div class="section-block quick-actions-block">
      <div class="section-header">
        <div>
          <div class="section-title">快捷操作</div>
          <div class="section-subtitle">一键进入高频现场动作</div>
        </div>
      </div>
      <div class="action-grid">
        <div class="action-card primary" @click="goToScan">
          <div class="action-icon"><van-icon name="scan" /></div>
          <div class="action-title">开始扫码录入</div>
          <div class="action-desc">接收 / 发出</div>
        </div>
        <div class="action-card" @click="goToPendingReceive">
          <div class="action-icon blue"><van-icon name="down" /></div>
          <div class="action-title">查看待接收</div>
          <div class="action-desc">上道已发出</div>
        </div>
        <div class="action-card" @click="goToPendingShip">
          <div class="action-icon orange"><van-icon name="upgrade" /></div>
          <div class="action-title">查看待发出</div>
          <div class="action-desc">本厂待交付</div>
        </div>
        <div class="action-card" @click="goToNotifications">
          <van-badge :content="unreadCount" :show-zero="false" max="99" class="action-badge">
            <div class="action-icon green"><van-icon name="bell" /></div>
          </van-badge>
          <div class="action-title">异常提醒</div>
          <div class="action-desc">{{ unreadCount > 0 ? `${unreadCount} 条未读` : '暂无未读' }}</div>
        </div>
      </div>
    </div>

    <div class="section-block">
      <van-cell title="外协流转雷达" label="查看全部订单、厂家与工序卡点" icon="chart-trending-o" is-link @click="goToKanban" />
      <van-cell title="我的通知" label="异常、超时与流转提醒，通知即待办" icon="bell" is-link @click="goToNotifications">
        <template #value>
          <van-badge v-if="unreadCount > 0" :content="unreadCount" max="99" />
        </template>
      </van-cell>
      <van-cell title="数据导出" label="按日期、厂家、状态导出Excel" icon="description" is-link @click="goToExport" />
    </div>

    <div class="logout-section">
      <van-button type="default" size="large" round @click="handleLogout" class="logout-button">
        退出登录
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useKanbanStore } from '@/stores/kanban'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const kanbanStore = useKanbanStore()
const { stats } = storeToRefs(kanbanStore)

const userInfo = computed(() => authStore.userInfo)
const unreadCount = computed(() => notificationStore.unreadCount)

const roleMap: Record<string, string> = {
  enterprise_admin: '企业管理员',
  factory_admin: '厂家管理员',
  factory_operator: '厂家操作员',
  operator: '操作员',
  admin: '管理员'
}

const roleText = computed(() => {
  const role = userInfo.value?.role
  return role ? roleMap[role] || role : '-'
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

onMounted(() => {
  authStore.initFromStorage()
  notificationStore.fetchNotificationList()
  const factoryId = authStore.userInfo?.role !== 'enterprise_admin' ? authStore.userInfo?.factory_id : undefined
  kanbanStore.fetchStats(factoryId)
})

const goToScan = () => {
  router.push('/scan')
}

const goToNotifications = () => {
  router.push('/notifications')
}

const goToKanban = () => {
  router.push('/kanban')
}

const goToOverdue = () => {
  router.push({ path: '/kanban', query: { quick: 'overdue' } })
}

const goToPendingReceive = () => {
  router.push({ path: '/kanban', query: { quick: 'receive' } })
}

const goToPendingShip = () => {
  router.push({ path: '/kanban', query: { quick: 'ship' } })
}

const goToExport = () => {
  router.push('/export')
}

const handleLogout = () => {
  authStore.logout()
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f4f7fb;
  padding-bottom: 24px;
}

.hero-card {
  padding: 18px 16px 58px;
  color: #fff;
  background: linear-gradient(135deg, #2f6bff 0%, #6d5dfc 58%, #8f63ff 100%);
  border-bottom-left-radius: 24px;
  border-bottom-right-radius: 24px;
  box-shadow: 0 10px 28px rgba(47, 107, 255, 0.22);
}

.hero-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-wrap {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
}

.user-details {
  flex: 1;
  min-width: 0;
}

.hello {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
}

.role-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 7px;
  font-size: 12px;
  opacity: 0.95;
}

.role-pill {
  padding: 2px 8px;
  border-radius: 999px;
  color: #2f6bff;
  background: #fff;
  font-weight: 600;
}

.factory-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workbench-title {
  margin-top: 20px;
  font-size: 25px;
  font-weight: 900;
}

.workbench-subtitle {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.9;
}

.overview-card {
  margin-top: 16px;
  padding: 14px;
  border-radius: 18px;
  color: #24324b;
  background: rgba(255, 255, 255, 0.96);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.overview-title {
  font-size: 16px;
  font-weight: 800;
}

.overview-subtitle {
  margin-top: 3px;
  font-size: 12px;
  color: #8a96a8;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.overview-item {
  text-align: center;
}

.overview-num {
  font-size: 20px;
  font-weight: 800;
  color: #24324b;
}

.overview-num.pending,
.overview-num.overdue {
  color: #ff8f1f;
}

.overview-num.processing {
  color: #2f6bff;
}

.overview-num.completed {
  color: #13b45f;
}

.overview-label {
  margin-top: 4px;
  font-size: 11px;
  color: #7b8798;
}

.overview-alert,
.overview-ok {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.overview-alert {
  color: #d46b08;
  background: #fff7e6;
}

.overview-ok {
  color: #0f9f5d;
  background: #edf9f2;
}

.section-block {
  margin: 12px 12px 0;
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(31, 45, 61, 0.06);
}

.rhythm-block {
  margin-top: -42px;
  padding: 14px;
}

.quick-actions-block {
  padding: 14px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #202b3d;
}

.section-subtitle {
  margin-top: 3px;
  font-size: 12px;
  color: #8a96a8;
}

.rhythm-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rhythm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: #f7f9fc;
}

.rhythm-item.urgent {
  background: #fff7e6;
}

.step {
  width: 26px;
  height: 26px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: #fff;
  background: #2f6bff;
  font-size: 13px;
  font-weight: 800;
}

.rhythm-content {
  flex: 1;
  min-width: 0;
}

.rhythm-title {
  font-size: 14px;
  font-weight: 800;
  color: #202b3d;
}

.rhythm-desc {
  margin-top: 3px;
  font-size: 12px;
  color: #7b8798;
  line-height: 1.45;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.action-card {
  min-height: 92px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #f7f9fc;
  cursor: pointer;
  text-align: center;
}

.action-card:active,
.rhythm-item:active {
  transform: scale(0.98);
}

.action-card.primary {
  color: #fff;
  background: linear-gradient(135deg, #2f6bff, #53a1ff);
}

.action-icon {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  border-radius: 12px;
  font-size: 20px;
  color: #fff;
  background: rgba(255, 255, 255, 0.22);
}

.action-icon.blue {
  color: #2f6bff;
  background: #eaf1ff;
}

.action-icon.orange {
  color: #ff8f1f;
  background: #fff2df;
}

.action-icon.green {
  color: #13b45f;
  background: #e9f8ef;
}

.action-title {
  font-size: 13px;
  font-weight: 700;
}

.action-desc {
  margin-top: 3px;
  font-size: 11px;
  color: #8a96a8;
}

.action-card.primary .action-desc {
  color: rgba(255, 255, 255, 0.86);
}

.action-badge {
  display: block;
}

.logout-section {
  margin-top: 22px;
  padding: 0 16px;
}

.logout-button {
  border: 1px solid #e5e8ef;
  color: #667085;
  background: #fff;
}
</style>
