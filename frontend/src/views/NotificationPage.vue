<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="notification-page">
    <QuickNavStrip />
    <van-nav-bar
      title="异常队列"
      left-arrow
      @click-left="router.back()"
    >
      <template #right>
        <van-badge :content="unreadCount" :max="99" :show="unreadCount > 0">
          <span class="mark-all" @click="handleMarkAllRead">全部已读</span>
        </van-badge>
      </template>
    </van-nav-bar>

    <section class="summary-card">
      <div>
        <div class="eyebrow">通知即待办</div>
        <h2>先处理高风险</h2>
        <p>{{ riskSummary }}</p>
      </div>
      <div class="summary-number">
        <strong>{{ unreadCount }}</strong>
        <span>未读</span>
      </div>
    </section>

    <section class="queue-toolbar">
      <div class="queue-item danger">
        <span>{{ highRiskCount }}</span>
        <small>高风险</small>
      </div>
      <div class="queue-item">
        <span>{{ unreadTodoCount }}</span>
        <small>待处理</small>
      </div>
      <div class="queue-item">
        <span>{{ notifications.length }}</span>
        <small>全部通知</small>
      </div>
    </section>

    <div class="notification-list">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div
            v-for="item in sortedNotifications"
            :key="item.notif_id"
            class="notification-item"
            :class="{ unread: !isRead(item), risk: isHighRisk(item) }"
            @click="handleClick(item)"
          >
            <div class="notification-icon">
              <van-icon :name="isHighRisk(item) ? 'warning-o' : 'bell'" :class="{ 'unread-icon': !isRead(item) }" />
            </div>
            <div class="notification-content">
              <div class="notification-header">
                <span class="notification-title">{{ item.title }}</span>
                <van-tag :type="isHighRisk(item) ? 'danger' : isRead(item) ? 'default' : 'primary'" size="small">
                  {{ isHighRisk(item) ? '高风险' : isRead(item) ? '已读' : '待办' }}
                </van-tag>
              </div>
              <div class="notification-body">{{ item.content || '请进入关联业务确认处理进度' }}</div>
              <div class="notification-footer">
                <span class="notification-time">{{ formatTime(item.created_at) }}</span>
                <van-button size="small" type="primary" plain @click.stop="handleJump(item)">
                  跳转处理
                </van-button>
              </div>
              <div v-if="!isRead(item)" class="unread-dot"></div>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>

      <van-empty v-if="notifications.length === 0 && !loading" description="暂无异常待办" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import QuickNavStrip from '@/components/QuickNavStrip.vue'

const router = useRouter()
const notificationStore = useNotificationStore()
const { notifications, unreadCount } = storeToRefs(notificationStore)

const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)

const highRiskCount = computed(() => notifications.value.filter(isHighRisk).length)
const unreadTodoCount = computed(() => notifications.value.filter(item => !isRead(item)).length)
const riskSummary = computed(() => {
  if (highRiskCount.value > 0) return `发现 ${highRiskCount.value} 条异常通知，建议先进入订单处理。`
  if (unreadCount.value > 0) return '暂无高风险异常，按未读通知逐条确认即可。'
  return '当前没有未读异常，现场流转保持可追踪。'
})

const sortedNotifications = computed(() => {
  return [...notifications.value].sort((a, b) => {
    const riskDiff = Number(isHighRisk(b)) - Number(isHighRisk(a))
    if (riskDiff !== 0) return riskDiff
    const unreadDiff = Number(!isRead(b)) - Number(!isRead(a))
    if (unreadDiff !== 0) return unreadDiff
    return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  })
})

onMounted(async () => {
  await notificationStore.fetchNotificationList()
  finished.value = true
})

async function onLoad() {
  await notificationStore.fetchNotificationList()
  loading.value = false
  finished.value = true
}

async function onRefresh() {
  await notificationStore.fetchNotificationList()
  refreshing.value = false
  showToast('刷新成功')
}

function isRead(item: any): boolean {
  return item.is_read === true || item.is_read === 1 || item.is_read === '1' || item.is_read === 'true'
}

function isHighRisk(item: any): boolean {
  const text = `${item.notif_type || ''}${item.title || ''}${item.content || ''}`
  return /逾期|超期|异常|拒绝|失败|高风险|overdue|error|risk/i.test(text)
}

async function handleClick(item: any) {
  await markReadIfNeeded(item)
}

async function handleJump(item: any) {
  await markReadIfNeeded(item)
  if (item.jump_url) {
    router.push(item.jump_url)
    return
  }
  if (item.related_type === 'order' && item.related_id) {
    router.push(`/kanban/${item.related_id}`)
    return
  }
  if (item.related_type === 'record' && item.related_id) {
    router.push(`/view/${item.related_id}`)
    return
  }
  showToast('暂无关联业务详情')
}

async function markReadIfNeeded(item: any) {
  if (!isRead(item)) {
    await notificationStore.markAsRead(item.notif_id)
  }
}

async function handleMarkAllRead() {
  await notificationStore.markAllAsRead()
  showToast('已全部标记为已读')
}

function formatTime(time: string): string {
  if (!time) return '-'
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 24 * 60 * 60 * 1000) {
    if (diff < 60 * 1000) return '刚刚'
    if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}分钟前`
    return `${Math.floor(diff / 3600000)}小时前`
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.notification-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding-bottom: 16px;
}

.mark-all {
  font-size: 13px;
  color: #1989fa;
  cursor: pointer;
}

.summary-card {
  margin: 12px;
  padding: 16px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(135deg, #2447d8, #ff6b6b);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 8px 18px rgba(36, 71, 216, 0.18);
}

.eyebrow {
  font-size: 12px;
  opacity: 0.86;
  margin-bottom: 4px;
}

.summary-card h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.summary-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.92;
}

.summary-number {
  min-width: 64px;
  text-align: center;
  align-self: center;
}

.summary-number strong {
  display: block;
  font-size: 28px;
}

.summary-number span {
  font-size: 12px;
}

.queue-toolbar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 0 12px 12px;
}

.queue-item {
  background: #fff;
  border-radius: 12px;
  padding: 10px;
  text-align: center;
}

.queue-item span {
  display: block;
  color: #323233;
  font-size: 18px;
  font-weight: 700;
}

.queue-item small {
  color: #969799;
  font-size: 12px;
}

.queue-item.danger span {
  color: #ee0a24;
}

.notification-list {
  padding: 0 12px;
}

.notification-item {
  display: flex;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  cursor: pointer;
  position: relative;
  transition: box-shadow 0.2s;
}

.notification-item:active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.notification-item.unread {
  background: #f0f7ff;
}

.notification-item.risk {
  border-left: 4px solid #ee0a24;
}

.notification-icon {
  flex-shrink: 0;
  width: 36px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  font-size: 24px;
  color: #999;
}

.notification-icon .unread-icon {
  color: #1989fa;
}

.notification-content {
  flex: 1;
  margin-left: 10px;
  position: relative;
  min-width: 0;
}

.notification-header,
.notification-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.notification-title {
  font-weight: bold;
  font-size: 15px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.notification-body {
  margin: 8px 0 10px;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.unread-dot {
  position: absolute;
  top: 0;
  right: 0;
  width: 8px;
  height: 8px;
  background: #ff4d4f;
  border-radius: 50%;
}
</style>
