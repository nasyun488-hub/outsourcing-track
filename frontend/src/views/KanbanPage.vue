<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="kanban-page">
    <QuickNavStrip />
    <div class="kanban-hero">
      <div class="hero-title-row">
        <div>
          <div class="hero-title">外协流转雷达</div>
          <div class="hero-subtitle">按当前卡点、流转进度与风险优先级巡检订单</div>
        </div>
        <van-icon name="replay" size="22" color="#fff" @click="reload" />
      </div>

      <div class="stats-cards">
        <div class="stat-card" :class="{ active: filterStatus === '' }" @click="selectStatus('')">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">全部</div>
        </div>
        <div class="stat-card" :class="{ active: filterStatus === 'pending' }" @click="selectStatus('pending')">
          <div class="stat-num pending">{{ stats.pending }}</div>
          <div class="stat-label">待处理</div>
        </div>
        <div class="stat-card" :class="{ active: filterStatus === 'in_progress' }" @click="selectStatus('in_progress')">
          <div class="stat-num processing">{{ stats.in_progress }}</div>
          <div class="stat-label">进行中</div>
        </div>
        <div class="stat-card" :class="{ active: filterStatus === 'completed' }" @click="selectStatus('completed')">
          <div class="stat-num completed">{{ stats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div v-if="stats.overdue_count" class="overdue-summary">
        <van-icon name="warning-o" /> {{ stats.overdue_count }} 条超时记录需关注
      </div>
    </div>

    <div class="radar-panel mobile-only">
      <div class="radar-panel-title">快捷筛选</div>
      <div class="quick-chip-row">
        <van-tag
          v-for="chip in quickFilters"
          :key="chip.value"
          class="quick-chip"
          :type="activeQuick === chip.value ? chip.type : 'default'"
          round
          size="medium"
          @click="selectQuick(chip.value)"
        >
          {{ chip.label }}
        </van-tag>
      </div>
    </div>

    <van-tabs v-model:active="filterStatus" class="filter-tabs mobile-only" line-width="22" @change="reload">
      <van-tab title="全部" name="" />
      <van-tab title="待处理" name="pending" />
      <van-tab title="进行中" name="in_progress" />
      <van-tab title="已完成" name="completed" />
    </van-tabs>

    <div class="filter-panel mobile-only">
      <div class="filter-panel-header" @click="filterExpanded = !filterExpanded">
        <div class="filter-title">
          <van-icon name="filter-o" /> 筛选条件
          <van-tag v-if="activeFilterCount" type="primary" size="mini">{{ activeFilterCount }}项</van-tag>
        </div>
        <div class="filter-toggle">
          {{ filterExpanded ? '收起' : '展开' }}
          <van-icon :name="filterExpanded ? 'arrow-up' : 'arrow-down'" />
        </div>
      </div>
      <div v-show="filterExpanded" class="filter-body">
        <van-field v-model="keyword" label="关键词" placeholder="订单号、制件、件号" clearable @blur="reload" />
        <van-field
          v-if="isEnterpriseAdmin"
          v-model="factoryKeyword"
          label="厂家ID"
          placeholder="输入厂家ID过滤"
          clearable
          @blur="reload"
        />
        <div class="date-row">
          <van-field v-model="startDate" label="开始" placeholder="YYYY-MM-DD" clearable @blur="reload" />
          <van-field v-model="endDate" label="结束" placeholder="YYYY-MM-DD" clearable @blur="reload" />
        </div>
        <div class="filter-actions">
          <van-button size="small" type="primary" round @click="reload">筛选</van-button>
          <van-button size="small" round @click="resetFilters">重置</van-button>
        </div>
      </div>
    </div>

    <section class="desktop-only pc-toolbar kanban-pc-toolbar">
      <div>
        <h3>订单流转工作台</h3>
        <p>集中筛选订单状态、厂家与风险，支持卡片 / 表格双视图巡检。</p>
      </div>
      <div class="pc-actions">
        <input v-model="keyword" class="pc-input" placeholder="订单号、制件、件号" @keyup.enter="reload" />
        <input v-if="isEnterpriseAdmin" v-model="factoryKeyword" class="pc-input" placeholder="厂家ID" @keyup.enter="reload" />
        <button type="button" :class="{ active: filterStatus === '' }" @click="selectStatus('')">全部</button>
        <button type="button" :class="{ active: filterStatus === 'pending' }" @click="selectStatus('pending')">待处理</button>
        <button type="button" :class="{ active: filterStatus === 'in_progress' }" @click="selectStatus('in_progress')">进行中</button>
        <button type="button" :class="{ active: filterStatus === 'completed' }" @click="selectStatus('completed')">已完成</button>
        <button type="button" @click="viewMode = 'card'" :class="{ active: viewMode === 'card' }">卡片视图</button>
        <button type="button" class="table-view" @click="viewMode = 'table'" :class="{ active: viewMode === 'table' }">表格视图</button>
        <button type="button" class="primary" @click="reload">刷新</button>
      </div>
    </section>

    <section v-if="viewMode === 'table'" class="desktop-only pc-data-table">
      <div class="table-title">订单流转表</div>
      <table>
        <thead>
          <tr>
            <th>订单号</th>
            <th>产品</th>
            <th>厂家</th>
            <th>状态</th>
            <th>数量</th>
            <th>进度</th>
            <th>风险</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in filteredOrders" :key="order.order_id">
            <td>{{ order.order_no }}</td>
            <td>{{ order.product_name || order.part_no || order.product_code || '-' }}</td>
            <td>{{ order.factory_name || order.factory_id || '-' }}</td>
            <td><span class="pc-status">{{ getStatusText(order.status) }}</span></td>
            <td>{{ order.quantity }}{{ order.unit || '件' }}</td>
            <td>{{ getProgressText(order) }}</td>
            <td>{{ getRiskText(order) }}</td>
            <td><button type="button" class="link-btn" @click="goToDetail(order.order_id)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
      <van-empty v-if="filteredOrders.length === 0 && !loading" description="暂无匹配订单" />
    </section>

    <div v-else class="desktop-only pc-data-table pc-card-board">
      <div class="table-title">订单卡片视图</div>
      <div class="pc-card-grid">
        <div v-for="order in filteredOrders" :key="order.order_id" class="pc-order-card" @click="goToDetail(order.order_id)">
          <strong>{{ order.order_no }}</strong>
          <span>{{ order.product_name || order.part_no || '-' }}</span>
          <small>{{ getCurrentCheckpoint(order) }}</small>
        </div>
      </div>
    </div>

    <div class="order-list mobile-only">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div
            v-for="order in filteredOrders"
            :key="order.order_id"
            class="order-item"
            :class="{ overdue: order.is_overdue }"
            @click="goToDetail(order.order_id)"
          >
            <div class="order-header">
              <div class="order-title-wrap">
                <span class="order-no">{{ order.order_no }}</span>
                <span v-if="order.is_overdue" class="overdue-dot">超时</span>
              </div>
              <van-tag :type="getStatusType(order.status)" size="small" round>
                {{ getStatusText(order.status) }}
              </van-tag>
            </div>

            <div class="product-name">{{ order.product_name || order.part_no || order.product_code || '-' }}</div>
            <div class="meta-line">
              <span>件号：{{ order.part_no || order.product_code || '-' }}</span>
              <span v-if="order.spec">规格：{{ order.spec }}</span>
            </div>

            <div class="checkpoint-card">
              <div>
                <span class="checkpoint-label">当前卡点</span>
                <div class="checkpoint-value">{{ getCurrentCheckpoint(order) }}</div>
              </div>
              <div class="progress-summary">
                <span class="checkpoint-label">流转进度</span>
                <div class="checkpoint-value">{{ getProgressText(order) }}</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-chip">
                <span class="label">数量</span>
                <span class="value">{{ order.quantity }}{{ order.unit || '件' }}</span>
              </div>
              <div class="info-chip wide">
                <span class="label">厂家</span>
                <span class="value ellipsis">{{ order.factory_name || order.factory_id || '-' }}</span>
              </div>
              <div class="info-chip">
                <span class="label">风险</span>
                <span class="value risk-value">{{ getRiskText(order) }}</span>
              </div>
            </div>

            <div class="process-row">
              <div class="process-bar">
                <div class="process-bar-inner" :style="{ width: getProgressPercent(order) }"></div>
              </div>
              <div class="process-counts">
                <span>待 {{ order.pending_count || 0 }}</span>
                <span>中 {{ order.in_progress_count || 0 }}</span>
                <span>完 {{ order.completed_count || 0 }}</span>
              </div>
            </div>

            <van-icon name="arrow" class="arrow-icon" />
          </div>
          <van-empty v-if="filteredOrders.length === 0 && !loading" description="暂无匹配订单" />
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKanbanStore, type Order } from '../stores/kanban'
import { useAuthStore } from '../stores/auth'
import { storeToRefs } from 'pinia'
import QuickNavStrip from '@/components/QuickNavStrip.vue'

const router = useRouter()
const route = useRoute()
const kanbanStore = useKanbanStore()
const authStore = useAuthStore()
const { orderList, stats } = storeToRefs(kanbanStore)

const filterStatus = ref('')
const keyword = ref('')
const factoryKeyword = ref('')
const startDate = ref('')
const endDate = ref('')
const filterExpanded = ref(false)
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const activeQuick = ref<string>((route.query.quick as string) || '')
const viewMode = ref<'card' | 'table'>('table')

const quickFilters: Array<{ label: string; value: string; type: 'primary' | 'success' | 'warning' | 'danger' }> = [
  { label: '我厂相关', value: 'mine', type: 'primary' },
  { label: '待我处理', value: 'todo', type: 'warning' },
  { label: '已逾期', value: 'overdue', type: 'danger' },
  { label: '今日更新', value: 'today', type: 'success' },
  { label: '即将超期', value: 'soon', type: 'warning' }
]

const isEnterpriseAdmin = computed(() => authStore.userInfo?.role === 'enterprise_admin')

const filterParams = computed(() => {
  const params: any = {}
  const userRole = authStore.userInfo?.role
  const factoryId = authStore.userInfo?.factory_id

  if (filterStatus.value) {
    params.status = filterStatus.value
  }
  if (keyword.value.trim()) {
    params.order_no = keyword.value.trim()
  }
  if (startDate.value.trim()) {
    params.start_date = `${startDate.value.trim()}T00:00:00`
  }
  if (endDate.value.trim()) {
    params.end_date = `${endDate.value.trim()}T23:59:59`
  }

  if (userRole !== 'enterprise_admin' && factoryId) {
    params.factory_id = factoryId
  } else if (factoryKeyword.value.trim()) {
    params.factory_id = factoryKeyword.value.trim()
  }

  if (activeQuick.value) {
    params.quick = activeQuick.value
  }

  return params
})

const activeFilterCount = computed(() => {
  return [keyword.value, factoryKeyword.value, startDate.value, endDate.value, activeQuick.value].filter(v => v.trim()).length
})

const filteredOrders = computed(() => {
  const factoryId = authStore.userInfo?.factory_id
  const today = new Date().toISOString().slice(0, 10)
  return orderList.value.filter(order => {
    const raw = order as Order & { updated_at?: string; updated_time?: string; due_at?: string }
    if (activeQuick.value === 'mine') {
      return !factoryId || order.factory_id === factoryId
    }
    if (activeQuick.value === 'todo') {
      return order.status === 'pending' || order.status === 'in_progress'
    }
    if (activeQuick.value === 'overdue') {
      return order.is_overdue
    }
    if (activeQuick.value === 'today') {
      const updatedAt = raw.updated_at || raw.updated_time || ''
      return updatedAt ? updatedAt.startsWith(today) : order.status !== 'completed'
    }
    if (activeQuick.value === 'soon') {
      return !order.is_overdue && order.status === 'in_progress'
    }
    if (activeQuick.value === 'receive' || activeQuick.value === 'ship') {
      return order.status === 'pending' || order.status === 'in_progress'
    }
    return true
  })
})

onMounted(async () => {
  authStore.initFromStorage()
  await reload()
})

async function onLoad() {
  await kanbanStore.fetchOrders(filterParams.value)
  loading.value = false
  finished.value = true
}

async function onRefresh() {
  await Promise.all([
    kanbanStore.fetchOrders(filterParams.value),
    kanbanStore.fetchStats()
  ])
  refreshing.value = false
}

async function reload() {
  loading.value = true
  finished.value = false
  await Promise.all([
    kanbanStore.fetchOrders(filterParams.value),
    kanbanStore.fetchStats()
  ])
  loading.value = false
  finished.value = true
}

async function selectStatus(status: string) {
  filterStatus.value = status
  await reload()
}

async function selectQuick(value: string) {
  activeQuick.value = activeQuick.value === value ? '' : value
  await reload()
}

async function resetFilters() {
  keyword.value = ''
  factoryKeyword.value = ''
  startDate.value = ''
  endDate.value = ''
  filterStatus.value = ''
  activeQuick.value = ''
  await reload()
}

function goToDetail(orderId: string) {
  router.push(`/kanban/${orderId}`)
}

function getCurrentCheckpoint(order: Order) {
  if (order.is_overdue) return '已逾期，需立即确认责任工序'
  if (order.pending_count > 0) return `等待接收 ${order.pending_count} 道工序`
  if (order.in_progress_count > 0) return `加工中 ${order.in_progress_count} 道工序`
  if (order.completed_count >= order.process_count && order.process_count > 0) return '全部工序已完成'
  return '等待首道工序启动'
}

function getRiskText(order: Order) {
  if (order.is_overdue) return '已逾期'
  if (order.status === 'in_progress') return '即将超期'
  if (order.status === 'pending') return '待我处理'
  return '正常'
}

function getProgressText(order: Order) {
  const total = order.process_count || 0
  if (!total) return '0/0'
  const current = Math.min(total, (order.completed_count || 0) + ((order.in_progress_count || 0) > 0 ? 1 : 0))
  return `${current}/${total}`
}

function getProgressPercent(order: Order) {
  const total = order.process_count || 0
  if (!total) return '0%'
  const current = Math.min(total, (order.completed_count || 0) + ((order.in_progress_count || 0) > 0 ? 1 : 0))
  return `${Math.round((current / total) * 100)}%`
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success'
  }
  return types[status] || 'default'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}
</script>

<style scoped>
.kanban-page {
  min-height: 100vh;
  background: #f4f7fb;
  padding-bottom: 20px;
}

.kanban-hero {
  padding: 18px 14px 42px;
  color: #fff;
  background: linear-gradient(135deg, #1e63ff 0%, #4d7cff 58%, #775cff 100%);
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0 8px 24px rgba(30, 99, 255, 0.22);
}

.hero-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.hero-title {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 0.5px;
}

.hero-subtitle {
  margin-top: 5px;
  font-size: 12px;
  opacity: 0.84;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 9px;
  margin-top: 16px;
}

.stat-card {
  text-align: center;
  padding: 11px 4px 10px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.16);
  cursor: pointer;
  backdrop-filter: blur(4px);
}

.stat-card.active {
  background: #fff;
  box-shadow: 0 8px 18px rgba(27, 56, 120, 0.15);
}

.stat-card.active .stat-label {
  color: #6b7586;
}

.stat-card:active,
.quick-chip:active {
  transform: scale(0.98);
}

.stat-num {
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}

.stat-card.active .stat-num {
  color: #263348;
}

.stat-num.pending,
.stat-card.active .stat-num.pending {
  color: #ff9d28;
}

.stat-num.processing,
.stat-card.active .stat-num.processing {
  color: #1e63ff;
}

.stat-num.completed,
.stat-card.active .stat-num.completed {
  color: #12b76a;
}

.stat-label {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.82);
}

.overdue-summary {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 12px;
  color: #fff7e6;
  background: rgba(255, 151, 106, 0.22);
}

.radar-panel {
  margin: -26px 10px 10px;
  padding: 12px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(31, 45, 61, 0.08);
}

.radar-panel-title {
  margin-bottom: 9px;
  font-size: 14px;
  font-weight: 800;
  color: #202b3d;
}

.quick-chip-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.quick-chip {
  flex: none;
  cursor: pointer;
}

.filter-tabs {
  margin: 10px 10px 0;
  overflow: hidden;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(31, 45, 61, 0.06);
}

.filter-panel {
  margin: 10px 10px 12px;
  overflow: hidden;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 4px 14px rgba(31, 45, 61, 0.06);
}

.filter-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 13px;
  font-size: 13px;
}

.filter-title,
.filter-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
}

.filter-title {
  font-weight: 700;
  color: #253044;
}

.filter-toggle {
  color: #7a8699;
}

.filter-body {
  border-top: 1px solid #f0f2f5;
}

.date-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.date-row :deep(.van-field__label) {
  width: 34px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 8px 12px 12px;
}

.order-list {
  padding: 0 10px;
}

.order-item {
  position: relative;
  margin-bottom: 10px;
  padding: 13px 34px 13px 13px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 5px 16px rgba(31, 45, 61, 0.07);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.order-item:active {
  transform: scale(0.99);
  box-shadow: 0 2px 8px rgba(31, 45, 61, 0.12);
}

.order-item.overdue {
  border: 1px solid #ffccc7;
  background: linear-gradient(0deg, #fff, #fff7f6);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.order-title-wrap {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.order-no {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 800;
  font-size: 15px;
  color: #1f2937;
}

.overdue-dot {
  flex: none;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  color: #ee0a24;
  background: #ffecec;
}

.product-name {
  margin-bottom: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #303b4f;
}

.meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: 5px 12px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #7a8699;
}

.checkpoint-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 12px;
  background: #eef4ff;
}

.checkpoint-label {
  display: block;
  margin-bottom: 3px;
  font-size: 11px;
  color: #6b7586;
}

.checkpoint-value {
  font-size: 13px;
  font-weight: 800;
  color: #1e63ff;
  line-height: 1.35;
}

.progress-summary {
  flex: none;
  text-align: right;
}

.info-grid {
  display: grid;
  grid-template-columns: 0.86fr 1.34fr 0.8fr;
  gap: 7px;
}

.info-chip {
  min-width: 0;
  padding: 7px 8px;
  border-radius: 10px;
  background: #f7f9fc;
}

.info-chip .label {
  display: block;
  margin-bottom: 3px;
  font-size: 10px;
  color: #98a2b3;
}

.info-chip .value {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #344054;
}

.info-chip .ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-value {
  color: #ff8f1f !important;
}

.process-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 11px;
}

.process-bar {
  flex: 1;
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f7;
}

.process-bar-inner {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #1e63ff, #12b76a);
}

.process-counts {
  display: flex;
  gap: 6px;
  flex: none;
  font-size: 11px;
  color: #7a8699;
}

.arrow-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #c8d0dc;
}

.desktop-only { display: block; }
.mobile-only { display: none; }
.pc-toolbar,
.pc-data-table {
  margin: 16px 24px;
  padding: 18px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(31, 45, 61, 0.08);
}
.pc-toolbar { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.pc-toolbar h3 { margin: 0 0 6px; font-size: 20px; color: #1f2937; }
.pc-toolbar p { margin: 0; color: #667085; font-size: 13px; }
.pc-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.pc-actions button,
.link-btn { border: 1px solid #d0d5dd; background: #fff; border-radius: 8px; padding: 8px 12px; color: #344054; cursor: pointer; }
.pc-actions button.active,
.pc-actions button.primary { color: #fff; border-color: #1e63ff; background: #1e63ff; }
.pc-input { min-width: 180px; border: 1px solid #d0d5dd; border-radius: 8px; padding: 8px 10px; }
.table-title { margin-bottom: 12px; font-weight: 800; color: #1f2937; }
.pc-data-table table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pc-data-table th,
.pc-data-table td { padding: 12px; border-bottom: 1px solid #eef2f7; text-align: left; }
.pc-data-table th { color: #667085; background: #f8fafc; font-weight: 700; }
.pc-status { padding: 3px 8px; border-radius: 999px; background: #eef4ff; color: #1e63ff; }
.link-btn { padding: 6px 10px; color: #1e63ff; border-color: #bfdbfe; }
.pc-card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.pc-order-card { padding: 14px; border: 1px solid #eef2f7; border-radius: 12px; cursor: pointer; }
.pc-order-card strong,
.pc-order-card span,
.pc-order-card small { display: block; margin-bottom: 6px; }

@media (max-width: 900px) {
  .desktop-only { display: none !important; }
  .mobile-only { display: block; }
}
</style>
