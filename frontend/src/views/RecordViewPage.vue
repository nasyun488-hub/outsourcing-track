<template>
  <div class="record-view-page">
    <van-nav-bar
      title="流转凭证"
      left-arrow
      @click-left="goBack"
      right-text="刷新"
      @click-right="loadData"
    />

    <!-- 加载状态 -->
    <van-loading v-if="loading" type="spinner" class="loading" />

    <template v-else-if="recordInfo">
      <div class="voucher-card">
        <div class="voucher-kicker">流转凭证</div>
        <div class="voucher-title">扫码来源可追溯</div>
        <div class="voucher-desc">关联订单、当前工序状态与收发批次集中留痕，便于现场复核。</div>
        <div class="voucher-grid">
          <div>
            <span class="label">关联订单</span>
            <span class="value">{{ recordInfo.order_id }}</span>
          </div>
          <div>
            <span class="label">当前工序状态</span>
            <span class="value">{{ statusText }}</span>
          </div>
        </div>
        <van-button round block plain type="primary" class="detail-back-btn" @click="goOrderDetail">
          返回订单详情
        </van-button>
      </div>

      <!-- 订单信息卡片 -->
      <div class="order-card">
        <div class="order-header">
          <div class="order-title">
            <span class="order-id">关联订单：{{ recordInfo.order_id }}</span>
            <van-tag :type="statusTagType" size="medium">
              {{ statusText }}
            </van-tag>
          </div>
          <div class="process-info">
            当前工序状态：第{{ recordInfo.process_seq }}道工序 {{ recordInfo.process_name }}｜{{ statusText }}
          </div>
          <div class="factory-info">
            厂家：{{ recordInfo.factory_name }}
          </div>
        </div>

        <!-- 锁定状态标识 -->
        <div class="lock-status">
          <van-tag
            v-if="recordInfo.entry_lock"
            type="danger"
            size="small"
            icon="lock"
          >
            录入锁定
          </van-tag>
          <van-tag
            v-if="recordInfo.relation_lock"
            type="warning"
            size="small"
            icon="link"
          >
            关联锁定
          </van-tag>
          <van-tag
            v-if="recordInfo.sync_lock"
            type="primary"
            size="small"
            icon="sync"
          >
            同步锁定
          </van-tag>
        </div>

        <!-- 超期提示 -->
        <div v-if="recordInfo.is_overdue" class="overdue-tip">
          <van-icon name="warning-o" />
          该工序已超期48小时未发出
        </div>
      </div>

      <!-- 接收记录 -->
      <van-cell-group inset title="接收记录" style="margin-top: 12px;">
        <template v-if="recordInfo.receive_batches && recordInfo.receive_batches.length > 0">
          <van-cell
            v-for="(item, index) in recordInfo.receive_batches"
            :key="index"
            :label="`批次${item.batch_no}`"
          >
            <template #title>
              <div class="record-item">
                <span class="record-time">{{ formatTime(item.receive_time) }}</span>
                <span class="record-count">×{{ item.receive_qty }}</span>
              </div>
            </template>
            <template #value>
              <span class="record-user">{{ item.receiver_name }}</span>
            </template>
          </van-cell>
        </template>
        <van-empty v-else description="暂无接收记录" />
      </van-cell-group>

      <!-- 发出记录 -->
      <van-cell-group inset title="发出记录" style="margin-top: 12px;">
        <template v-if="recordInfo.ship_batches && recordInfo.ship_batches.length > 0">
          <van-cell
            v-for="(item, index) in recordInfo.ship_batches"
            :key="index"
            :label="`批次${item.batch_no}`"
          >
            <template #title>
              <div class="record-item">
                <span class="record-time">{{ formatTime(item.ship_time) }}</span>
                <span class="record-count">×{{ item.ship_qty }}</span>
              </div>
            </template>
            <template #value>
              <div class="ship-info">
                <span class="record-user">{{ item.shipper_name }}</span>
                <van-tag
                  v-if="item.is_return"
                  type="warning"
                  size="small"
                >
                  退件
                </van-tag>
              </div>
            </template>
          </van-cell>
          <!-- 退件详情 -->
          <template v-for="(item, index) in recordInfo.ship_batches.filter(r => r.is_return)" :key="'return-' + index">
            <van-cell title="退件原因" :value="item.return_reason || ''" />
            <van-cell title="退件数量" :value="String(item.return_qty || 0)" />
          </template>
        </template>
        <van-empty v-else description="暂无发出记录" />
      </van-cell-group>

      <!-- 退件记录 -->
      <van-cell-group inset title="退件记录" style="margin-top: 12px;">
        <template v-if="recordInfo.returns && recordInfo.returns.length > 0">
          <van-cell
            v-for="item in recordInfo.returns"
            :key="item.return_id"
            title="退件流水"
            :label="item.return_reason || '未填写原因'"
            :value="`×${item.return_qty}`"
          />
        </template>
        <van-empty v-else description="暂无退件记录" />
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="action-buttons" v-if="recordInfo.lock_type !== 'sync_lock'">
        <van-button
          type="primary"
          round
          block
          @click="goToReceive"
          :disabled="recordInfo.status === 'completed' || recordInfo.lock_type === 'relation_lock'"
        >
          接收
        </van-button>
        <van-button
          type="success"
          round
          block
          @click="goToShip"
          :disabled="recordInfo.status === 'pending' || recordInfo.lock_type === 'relation_lock'"
        >
          发出
        </van-button>
      </div>
    </template>

    <van-empty v-else description="未找到订单信息" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { getRecordDetail, type RecordInfo } from '@/api/records'

const router = useRouter()
const route = useRoute()

const record_id = computed(() => route.params.record_id as string)

const loading = ref(false)
const recordInfo = ref<RecordInfo | null>(null)

const statusTagType = computed(() => {
  switch (recordInfo.value?.status) {
    case 'pending': return 'default'
    case 'received': return 'primary'
    case 'shipped': return 'success'
    case 'completed': return 'success'
    default: return 'default'
  }
})

const statusText = computed(() => {
  switch (recordInfo.value?.status) {
    case 'pending': return '待接收'
    case 'received': return '已接收'
    case 'shipped': return '已发出'
    case 'completed': return '已完成'
    default: return '未知'
  }
})

const goBack = () => {
  router.back()
}

const goOrderDetail = () => {
  if (recordInfo.value?.order_id) {
    router.push(`/kanban/${recordInfo.value.order_id}`)
  }
}

const formatTime = (time: string): string => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getRecordDetail(record_id.value)
    recordInfo.value = res
  } catch (err) {
    console.error('获取订单详情失败:', err)
    showToast('获取订单详情失败')
  } finally {
    loading.value = false
  }
}

const goToReceive = () => {
  router.push(`/receive/${record_id.value}`)
}

const goToShip = () => {
  router.push(`/ship/${record_id.value}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.record-view-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 20px;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.order-card {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.voucher-card {
  margin: 12px;
  padding: 16px;
  color: #fff;
  border-radius: 14px;
  background: linear-gradient(135deg, #1989fa, #6aa9ff);
  box-shadow: 0 8px 20px rgba(25, 137, 250, 0.2);
}

.voucher-kicker {
  font-size: 12px;
  opacity: 0.86;
}

.voucher-title {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 800;
}

.voucher-desc {
  margin-top: 6px;
  font-size: 13px;
  line-height: 19px;
  opacity: 0.92;
}

.voucher-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.voucher-grid > div {
  min-width: 0;
  padding: 9px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.18);
}

.voucher-grid .label,
.voucher-grid .value {
  display: block;
}

.voucher-grid .label {
  font-size: 12px;
  opacity: 0.86;
}

.voucher-grid .value {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 700;
  word-break: break-all;
}

.detail-back-btn {
  margin-top: 12px;
  background: #fff;
}

.order-header {
  margin-bottom: 12px;
}

.order-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.order-id {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.process-info {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.factory-info {
  font-size: 13px;
  color: #999;
}

.lock-status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.overdue-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
  font-size: 13px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-time {
  color: #333;
}

.record-count {
  color: #07c160;
  font-weight: bold;
}

.record-user {
  color: #666;
}

.ship-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  padding: 16px;
  margin-top: 16px;
}

.action-buttons .van-button {
  flex: 1;
}
</style>
