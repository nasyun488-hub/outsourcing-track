<template>
  <div class="kanban-detail-page">
    <van-nav-bar
      title="订单作战室"
      left-text="返回"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    />

    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" size="40px">加载中...</van-loading>
    </div>

    <template v-else-if="order">
      <div class="battle-hero">
        <div class="hero-kicker">订单作战室</div>
        <div class="hero-title-row">
          <div class="hero-title">{{ order.product_name || '未填写制件' }}</div>
          <van-tag :type="getStatusType(order.status)" size="medium">
            {{ getStatusText(order.status) }}
          </van-tag>
        </div>
        <div class="summary-order">订单号：{{ order.order_no || order.order_id }}</div>
        <div class="hero-metrics">
          <div class="metric-card">
            <span class="label">总工序</span>
            <span class="value">{{ allProcessCount }}</span>
          </div>
          <div class="metric-card blue">
            <span class="label">可接收</span>
            <span class="value">{{ receiveReadyCount }}</span>
          </div>
          <div class="metric-card green">
            <span class="label">可发出</span>
            <span class="value">{{ shipReadyCount }}</span>
          </div>
          <div class="metric-card orange">
            <span class="label">等待上道发出</span>
            <span class="value">{{ waitingPrevCount }}</span>
          </div>
        </div>
      </div>

      <div class="next-step-card" :class="riskCardClass">
        <div class="section-title-row compact">
          <div>
            <div class="section-title">下一步建议</div>
            <div class="section-subtitle">先处理可操作工序，减少现场判断成本</div>
          </div>
          <van-tag v-if="primaryAction" :type="primaryAction.type" plain>{{ primaryAction.badge }}</van-tag>
          <van-tag v-else-if="riskLevel !== 'normal'" :type="riskTagType" plain>{{ riskLevelText }}</van-tag>
        </div>
        <div v-if="bottleneckProcess" class="bottleneck-strip">
          <div class="bottleneck-title">当前卡点：{{ bottleneckProcess.process_name || bottleneckProcess.process_id }}</div>
          <div class="bottleneck-desc">{{ riskReason || bottleneckProcess.risk_reason || '请关注该工序流转进度' }}</div>
        </div>
        <div class="advice-main">
          <van-icon :name="primaryAction ? 'todo-list-o' : 'passed'" />
          <span>{{ nextStepAdvice }}</span>
        </div>
        <div v-if="primaryAction" class="advice-actions">
          <van-button
            v-if="primaryAction.kind === 'receive'"
            type="primary"
            round
            block
            @click="goReceive(primaryAction.recordId)"
          >
            去接收 {{ primaryAction.qty }}
          </van-button>
          <van-button
            v-else
            type="success"
            round
            block
            @click="goShip(primaryAction.recordId)"
          >
            去发出 {{ primaryAction.qty }}
          </van-button>
        </div>
      </div>

      <div class="order-summary-card">
        <div class="summary-grid">
          <div class="summary-item">
            <span class="label">件号/规格</span>
            <span class="value">{{ order.part_no || '-' }} / {{ order.spec || '-' }}</span>
          </div>
          <div class="summary-item">
            <span class="label">数量</span>
            <span class="value strong">{{ order.quantity || 0 }} {{ order.unit || '件' }}</span>
          </div>
          <div class="summary-item full">
            <span class="label">主厂</span>
            <span class="value">{{ order.factory_name || '-' }}</span>
          </div>
        </div>
      </div>

      <div class="process-section">
        <div class="section-title-row">
          <div>
            <div class="section-title">工序流转时间线</div>
            <div class="section-subtitle">按工序顺序查看流转状态：等待上道发出 / 可接收 / 可发出 / 已完成</div>
          </div>
          <van-tag plain type="primary">共 {{ allProcessCount }} 道</van-tag>
        </div>

        <div class="flow-legend">
          <span><i class="dot waiting"></i>等待上道发出</span>
          <span><i class="dot receive"></i>可接收</span>
          <span><i class="dot ship"></i>可发出</span>
          <span><i class="dot done"></i>已完成</span>
        </div>

        <div class="timeline-list">
          <div v-for="process in visibleProcesses" :key="process.record_id" class="timeline-shell" :class="timelineClass(process)">
            <div class="timeline-marker"></div>
            <ProcessCard :process="process" :total-count="allProcessCount" />
          </div>
        </div>
        <div v-if="visibleProcesses.length === 0" class="empty-tip">
          暂无工序信息
        </div>
      </div>
    </template>

    <div v-else class="empty-tip">
      订单不存在
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKanbanStore, type Process } from '../stores/kanban'
import { useAuthStore } from '../stores/auth'
import ProcessCard from '../components/ProcessCard.vue'

const route = useRoute()
const router = useRouter()
const kanbanStore = useKanbanStore()
const authStore = useAuthStore()

const loading = ref(false)
const order = computed(() => kanbanStore.currentOrder)
const allProcessCount = computed(() => order.value?.processes?.length || 0)

const nonNegative = (value: unknown) => Math.max(Number(value || 0), 0)
const clampQty = (value: unknown, maxValue: number) => Math.min(nonNegative(value), Math.max(maxValue, 0))
const prevShipQtyOf = (process: Process) => nonNegative(process.prev_ship_qty)
const receiveQtyOf = (process: Process) => clampQty(process.current_receive_qty ?? process.receive_qty, Math.max(prevShipQtyOf(process), nonNegative(process.receive_qty)))
const shipQtyOf = (process: Process) => clampQty(process.current_ship_qty ?? process.ship_qty, receiveQtyOf(process))
const availableReceiveOf = (process: Process) => clampQty(process.available_receive_qty ?? (prevShipQtyOf(process) - receiveQtyOf(process)), prevShipQtyOf(process) - receiveQtyOf(process))
const availableShipOf = (process: Process) => clampQty(process.available_ship_qty ?? (receiveQtyOf(process) - shipQtyOf(process)), receiveQtyOf(process) - shipQtyOf(process))
const isWaitingPrev = (process: Process) => Boolean(process.prev_process_id && prevShipQtyOf(process) <= 0 && availableReceiveOf(process) <= 0)

const visibleProcesses = computed(() => {
  if (!order.value?.processes) return []

  const userRole = authStore.userInfo?.role
  const userFactoryId = authStore.userInfo?.factory_id
  const factoryRoles = ['factory_admin', 'factory_operator', 'primary_admin', 'primary_operator', 'cooperative_admin', 'cooperative_operator', 'operator']

  if (factoryRoles.includes(String(userRole))) {
    const processes = order.value.processes
    const myIndex = processes.findIndex(p => String(p.factory_id) === String(userFactoryId))
    if (myIndex === -1) return []

    const start = Math.max(0, myIndex - 1)
    const end = Math.min(processes.length, myIndex + 2)
    return processes.slice(start, end)
  }

  return order.value.processes
})

const receiveReadyProcesses = computed(() => visibleProcesses.value.filter(process => Boolean(process.can_receive)))
const shipReadyProcesses = computed(() => visibleProcesses.value.filter(process => Boolean(process.can_ship)))
const waitingProcesses = computed(() => visibleProcesses.value.filter(isWaitingPrev))
const receiveReadyCount = computed(() => receiveReadyProcesses.value.length)
const shipReadyCount = computed(() => shipReadyProcesses.value.length)
const waitingPrevCount = computed(() => waitingProcesses.value.length)
const detailMeta = computed(() => order.value?.detailMeta)
const riskLevel = computed(() => detailMeta.value?.risk_level || 'normal')
const riskReason = computed(() => detailMeta.value?.risk_reason || '')
const bottleneckProcess = computed(() => {
  const bottleneckId = detailMeta.value?.current_bottleneck_record_id
  if (bottleneckId) return visibleProcesses.value.find(process => process.record_id === bottleneckId) || null
  return visibleProcesses.value.find(process => process.is_bottleneck) || null
})
const riskTagType = computed(() => riskLevel.value === 'high' ? 'danger' : 'warning')
const riskLevelText = computed(() => riskLevel.value === 'high' ? '高风险' : '需关注')
const riskCardClass = computed(() => ({
  'risk-high': riskLevel.value === 'high',
  'risk-medium': riskLevel.value === 'medium'
}))

const primaryAction = computed(() => {
  const receiveProcess = receiveReadyProcesses.value[0]
  if (receiveProcess) {
    return {
      kind: 'receive' as const,
      recordId: receiveProcess.record_id,
      qty: availableReceiveOf(receiveProcess),
      badge: '可接收',
      type: 'primary' as const
    }
  }
  const shipProcess = shipReadyProcesses.value[0]
  if (shipProcess) {
    return {
      kind: 'ship' as const,
      recordId: shipProcess.record_id,
      qty: availableShipOf(shipProcess),
      badge: '可发出',
      type: 'success' as const
    }
  }
  return null
})

const nextStepAdvice = computed(() => {
  if (primaryAction.value?.kind === 'receive') return `建议先接收第 ${processOrderText(receiveReadyProcesses.value[0])} 道工序，本次可接收 ${primaryAction.value.qty}`
  if (primaryAction.value?.kind === 'ship') return `建议先发出第 ${processOrderText(shipReadyProcesses.value[0])} 道工序，本次可发出 ${primaryAction.value.qty}`
  const readOnlyReadyCount = visibleProcesses.value.filter(process => !process.can_operate && (availableReceiveOf(process) > 0 || availableShipOf(process) > 0)).length
  if (readOnlyReadyCount > 0) return `相邻厂家有 ${readOnlyReadyCount} 道工序可处理，你当前仅可查看，不能代操作。`
  if (waitingPrevCount.value > 0) return `当前有 ${waitingPrevCount.value} 道工序等待上道发出，可联系上道厂家推进。`
  return '暂无待操作工序，订单流转状态稳定。'
})

onMounted(async () => {
  const orderId = String(route.params.order_id)
  loading.value = true
  try {
    await kanbanStore.fetchDetail(orderId)
  } finally {
    loading.value = false
  }
})

function goBack() {
  router.back()
}

function goReceive(recordId: string) {
  router.push(`/receive/${recordId}`)
}

function goShip(recordId: string) {
  router.push(`/ship/${recordId}`)
}

function processOrderText(process?: Process) {
  return process?.process_order || process?.process_id || '-'
}

function timelineClass(process: Process) {
  return {
    waiting: isWaitingPrev(process),
    receivable: Boolean(process.can_receive),
    shippable: Boolean(process.can_ship),
    bottleneck: Boolean(process.is_bottleneck),
    risk: process.risk_level === 'high',
    done: receiveQtyOf(process) > 0 && shipQtyOf(process) >= receiveQtyOf(process)
  }
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'default'
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
  return texts[status] || status || '-'
}
</script>

<style scoped>
.kanban-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 12px;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.battle-hero {
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(135deg, #1b6cff 0%, #34b7ff 100%);
  box-shadow: 0 8px 20px rgba(25, 137, 250, 0.22);
}

.hero-kicker {
  font-size: 12px;
  opacity: 0.86;
  margin-bottom: 6px;
}

.hero-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.hero-title {
  flex: 1;
  font-size: 20px;
  line-height: 26px;
  font-weight: 800;
}

.summary-order {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.9;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 14px;
}

.metric-card {
  min-width: 0;
  padding: 9px 4px;
  text-align: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.18);
}

.metric-card .label {
  display: block;
  font-size: 11px;
  opacity: 0.9;
}

.metric-card .value {
  display: block;
  margin-top: 3px;
  font-size: 18px;
  line-height: 20px;
  font-weight: 800;
}

.next-step-card,
.order-summary-card,
.process-section {
  background: #fff;
  border-radius: 12px;
  padding: 14px 12px;
  margin-bottom: 12px;
}

.next-step-card {
  border: 1px solid #e8f3ff;
}

.next-step-card.risk-high {
  border-color: #ffccc7;
  background: linear-gradient(180deg, #fff7f6 0%, #fff 58%);
}

.next-step-card.risk-medium {
  border-color: #ffe1b3;
  background: linear-gradient(180deg, #fffaf2 0%, #fff 58%);
}

.bottleneck-strip {
  margin-bottom: 10px;
  padding: 9px 10px;
  border-radius: 10px;
  background: #fff7e8;
  border-left: 4px solid #ff976a;
}

.bottleneck-title {
  font-size: 14px;
  font-weight: 700;
  color: #663c00;
}

.bottleneck-desc {
  margin-top: 3px;
  font-size: 12px;
  line-height: 18px;
  color: #8a5a12;
}

.section-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.section-title-row.compact {
  margin-bottom: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.section-subtitle {
  margin-top: 3px;
  font-size: 12px;
  color: #999;
}

.advice-main {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #1989fa;
  background: #ecf5ff;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 20px;
}

.advice-actions {
  margin-top: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.summary-item {
  min-width: 0;
  background: #f7f8fa;
  border-radius: 8px;
  padding: 9px 10px;
}

.summary-item.full {
  grid-column: span 2;
}

.summary-item .label {
  display: block;
  color: #888;
  font-size: 12px;
  margin-bottom: 4px;
}

.summary-item .value {
  display: block;
  color: #333;
  font-weight: 600;
  font-size: 14px;
  word-break: break-all;
}

.summary-item .value.strong {
  color: #1989fa;
  font-size: 16px;
}

.flow-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
  color: #777;
  font-size: 12px;
  padding: 8px 10px;
  margin-bottom: 12px;
  background: #f7f8fa;
  border-radius: 8px;
}

.flow-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.dot.waiting { background: #ff976a; }
.dot.receive { background: #1989fa; }
.dot.ship { background: #07c160; }
.dot.done { background: #969799; }

.timeline-list {
  position: relative;
}

.timeline-shell {
  position: relative;
  padding-left: 16px;
  border-left: 2px solid #ebedf0;
}

.timeline-marker {
  position: absolute;
  left: -5px;
  top: 18px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c8c9cc;
  border: 2px solid #fff;
}

.timeline-shell.waiting .timeline-marker { background: #ff976a; }
.timeline-shell.receivable .timeline-marker { background: #1989fa; }
.timeline-shell.shippable .timeline-marker { background: #07c160; }
.timeline-shell.bottleneck .timeline-marker { box-shadow: 0 0 0 4px rgba(255, 151, 106, 0.18); }
.timeline-shell.risk .timeline-marker { background: #ee0a24; }
.timeline-shell.done .timeline-marker { background: #969799; }

.empty-tip {
  text-align: center;
  color: #999;
  padding: 30px 0;
  font-size: 14px;
}
</style>
