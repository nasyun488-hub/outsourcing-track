<template>
  <div class="process-card" :class="{ overdue: process.is_overdue, active: hasAction }">
    <div class="process-header">
      <div class="title-wrap">
        <span class="sequence-badge">第 {{ processOrderText }} 道</span>
        <span class="process-name">{{ process.process_name || '未知工序' }}</span>
      </div>
      <van-tag :type="statusTag.type" size="small">
        {{ statusTag.text }}
      </van-tag>
    </div>

    <div class="factory-line">
      <van-icon name="shop-o" />
      <span>{{ process.factory_name || '-' }}</span>
    </div>

    <div class="flow-line">
      <div class="flow-node" :class="{ muted: !process.prev_process_id }">
        {{ process.prev_process_id ? '上道' : '首道' }}
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-node current">本道</div>
      <div class="flow-arrow">→</div>
      <div class="flow-node" :class="{ muted: !process.next_process_id }">
        {{ process.next_process_id ? '下道' : '末道' }}
      </div>
    </div>

    <div class="quantity-panel">
      <div class="qty-card blue">
        <span class="label">可接收</span>
        <span class="num">{{ availableReceive }}</span>
      </div>
      <div class="qty-card green">
        <span class="label">可发出</span>
        <span class="num">{{ availableShip }}</span>
      </div>
      <div class="qty-card">
        <span class="label">累计接收</span>
        <span class="num">{{ receiveQty }}</span>
      </div>
      <div class="qty-card">
        <span class="label">累计发出</span>
        <span class="num">{{ shipQty }}</span>
      </div>
    </div>

    <div class="progress-wrap">
      <div class="progress-head">
        <span>发出进度</span>
        <span>{{ progressPercent }}%</span>
      </div>
      <van-progress :percentage="progressPercent" :show-pivot="false" color="#07c160" stroke-width="6" />
      <div class="progress-tip">上道发出 {{ prevShipQty }}，本次已收 {{ currentReceiveQty }}，本次已发 {{ currentShipQty }}</div>
    </div>

    <div class="status-tip" :class="statusTipClass">
      <van-icon :name="statusTipIcon" />
      <span>{{ statusTip }}</span>
    </div>

    <div class="action-row">
      <div class="action-item">
        <van-button size="small" block type="primary" plain :disabled="!canReceive" @click="goReceive">
          接收
        </van-button>
        <div v-if="!canReceive" class="disabled-reason">{{ receiveDisabledReason }}</div>
      </div>
      <div class="action-item">
        <van-button size="small" block type="success" plain :disabled="!canShip" @click="goShip">
          发出
        </van-button>
        <div v-if="!canShip" class="disabled-reason">{{ shipDisabledReason }}</div>
      </div>
      <div class="action-item detail">
        <van-button size="small" block plain @click="goView">详情</van-button>
      </div>
    </div>

    <div v-if="process.is_overdue" class="overdue-warning">
      <van-icon name="warning-o" />
      <span>该工序已超期，请优先处理</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Process } from '../stores/kanban'

const props = defineProps<{
  process: Process
  totalCount?: number
}>()

const router = useRouter()

const nonNegative = (value: unknown) => Math.max(Number(value || 0), 0)
const clampQty = (value: unknown, maxValue: number) => Math.min(nonNegative(value), nonNegative(maxValue))

// 展示层防御：所有流转数量不展示为负数，也不展示超过上道/订单可供量，避免异常数据误导“已发完”。
const prevShipQty = computed(() => nonNegative(props.process.prev_ship_qty))
const receiveQty = computed(() => clampQty(props.process.receive_qty, prevShipQty.value))
const shipQty = computed(() => clampQty(props.process.ship_qty, receiveQty.value))
const currentReceiveQty = computed(() => clampQty(props.process.current_receive_qty ?? receiveQty.value, prevShipQty.value))
const currentShipQty = computed(() => clampQty(props.process.current_ship_qty ?? shipQty.value, currentReceiveQty.value))
const availableReceive = computed(() => clampQty(props.process.available_receive_qty ?? (prevShipQty.value - receiveQty.value), prevShipQty.value - receiveQty.value))
const availableShip = computed(() => clampQty(props.process.available_ship_qty ?? (receiveQty.value - shipQty.value), receiveQty.value - shipQty.value))
const canReceive = computed(() => availableReceive.value > 0)
const canShip = computed(() => availableShip.value > 0)
const hasAction = computed(() => canReceive.value || canShip.value)
const processOrderText = computed(() => props.process.process_order || '-')

const progressBase = computed(() => Math.max(receiveQty.value, prevShipQty.value, 0))
const progressPercent = computed(() => {
  if (progressBase.value <= 0) return 0
  return Math.min(100, Math.round((shipQty.value / progressBase.value) * 100))
})

const receiveDisabledReason = computed(() => {
  if (prevShipQty.value <= 0 && props.process.prev_process_id) return '等待上道发出'
  if (availableReceive.value <= 0 && receiveQty.value > 0) return '暂无可接收余量'
  if (availableReceive.value <= 0) return '不可接收'
  return ''
})

const shipDisabledReason = computed(() => {
  if (receiveQty.value <= 0) return '需先接收'
  if (availableShip.value <= 0 && shipQty.value >= receiveQty.value) return '已全部发出'
  if (availableShip.value <= 0) return '暂无可发出余量'
  return ''
})

const statusTag = computed(() => {
  if (canReceive.value) return { type: 'primary', text: `待接收 ${availableReceive.value}` }
  if (canShip.value) return { type: 'success', text: `待发出 ${availableShip.value}` }
  if (receiveQty.value > 0 && shipQty.value >= receiveQty.value) return { type: 'default', text: '已发完' }
  return { type: getStatusTagType(props.process.status), text: getStatusText(props.process.status) }
})

const statusTip = computed(() => {
  if (canReceive.value && canShip.value) return `可接收 ${availableReceive.value}，可发出 ${availableShip.value}`
  if (canReceive.value) return `上道已发，可接收 ${availableReceive.value}`
  if (canShip.value) return `已接收待发出，可发出 ${availableShip.value}`
  if (shipQty.value >= receiveQty.value && receiveQty.value > 0) return '本道接收数量已全部发出'
  if (props.process.prev_process_id && prevShipQty.value <= 0) return '等待上道工序发出后接收'
  return '暂无可操作数量'
})

const statusTipClass = computed(() => ({
  ready: hasAction.value,
  done: !hasAction.value && receiveQty.value > 0 && shipQty.value >= receiveQty.value
}))

const statusTipIcon = computed(() => hasAction.value ? 'todo-list-o' : 'info-o')

function goReceive() {
  if (!canReceive.value) return
  router.push(`/receive/${props.process.record_id}`)
}

function goShip() {
  if (!canShip.value) return
  router.push(`/ship/${props.process.record_id}`)
}

function goView() {
  router.push(`/view/${props.process.record_id}`)
}

function getStatusTagType(status: string) {
  const types: Record<string, string> = {
    pending: 'warning',
    received: 'primary',
    shipped: 'info',
    completed: 'success',
    transferred: 'success'
  }
  return types[status] || 'default'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    pending: '待接收',
    received: '已接收',
    shipped: '已发出',
    completed: '已完成',
    transferred: '已转运'
  }
  return texts[status] || status || '-'
}
</script>

<style scoped>
.process-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
}

.process-card.active {
  border-color: #d7ebff;
}

.process-card.overdue {
  background: #fffafa;
  border-color: #ffccc7;
}

.process-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 9px;
}

.title-wrap {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.sequence-badge {
  color: #1989fa;
  background: #ecf5ff;
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 12px;
  font-weight: 600;
}

.process-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
}

.factory-line {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #666;
  font-size: 13px;
  margin-bottom: 10px;
}

.flow-line {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
}

.flow-node {
  text-align: center;
  font-size: 12px;
  color: #666;
  background: #f7f8fa;
  border-radius: 999px;
  padding: 5px 0;
}

.flow-node.current {
  color: #1989fa;
  background: #ecf5ff;
  font-weight: 600;
}

.flow-node.muted {
  color: #999;
  background: #f2f3f5;
}

.flow-arrow {
  color: #c8c9cc;
}

.quantity-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}

.qty-card {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 8px 4px;
  text-align: center;
}

.qty-card.blue { background: #ecf5ff; }
.qty-card.green { background: #f0fbf4; }

.qty-card .label {
  display: block;
  color: #888;
  font-size: 11px;
  margin-bottom: 3px;
}

.qty-card .num {
  color: #333;
  font-size: 16px;
  line-height: 18px;
  font-weight: 700;
}

.qty-card.blue .num { color: #1989fa; }
.qty-card.green .num { color: #07c160; }

.progress-wrap {
  margin-bottom: 10px;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 12px;
  margin-bottom: 5px;
}

.progress-tip {
  margin-top: 5px;
  color: #999;
  font-size: 12px;
}

.status-tip {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #666;
  background: #f7f8fa;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  margin-bottom: 10px;
}

.status-tip.ready {
  color: #1989fa;
  background: #ecf5ff;
}

.status-tip.done {
  color: #07c160;
  background: #f0fbf4;
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr 74px;
  gap: 8px;
  align-items: start;
}

.action-item.detail {
  align-self: start;
}

.disabled-reason {
  margin-top: 4px;
  color: #999;
  font-size: 11px;
  text-align: center;
  min-height: 14px;
}

.overdue-warning {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  color: #ee0a24;
  font-size: 13px;
  font-weight: 500;
}
</style>