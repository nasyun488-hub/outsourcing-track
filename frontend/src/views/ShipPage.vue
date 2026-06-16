<template>
  <div class="ship-page">
    <van-nav-bar
      title="发出操作台"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    />

    <div class="top-tip-card">
      <div class="tip-label">发出操作台｜本次可发出</div>
      <div class="tip-num">{{ availableShip }}</div>
      <div class="tip-desc">少输入：发出数量不能超过本道已接收未发出的余量，可一键填入全部可发出数量</div>
    </div>

    <div class="operation-guide-card">
      <div class="guide-title">本次可发出：{{ availableShip }}</div>
      <div class="guide-desc">提交后返回订单详情；退件不打断主流程，可在下方独立处理。</div>
      <div v-if="availableShip <= 0" class="guide-warning">
        <van-icon name="warning-o" />
        <span>{{ shipUnavailableText }}</span>
      </div>
    </div>

    <van-form @submit="handleSubmit" class="ship-form">
      <!-- 只读信息 -->
      <van-cell-group inset title="订单信息">
        <van-cell title="订单号" :value="orderInfo.order_id || record_id" />
        <van-cell title="工序" :value="processTitle" />
        <van-cell title="厂家" :value="orderInfo.factory_name || '-'" />
        <van-cell title="累计接收" :value="`${currentReceiveQty}`" />
        <van-cell title="累计发出" :value="`${currentShipQty}`" />
        <van-cell title="本次可发出" :value="`${availableShip}`" value-class="highlight-value" />
      </van-cell-group>

      <!-- 发出信息 -->
      <van-cell-group inset title="发出信息">
        <van-cell title="发出人" :value="userInfo?.name || '-'" />
        <van-field
          v-model="shipTime"
          is-link
          readonly
          label="发出时间"
          placeholder="请选择发出时间"
          @click="showTimePicker = true"
        />
        <van-field
          v-model.number="shipCount"
          type="number"
          label="发出数量"
          :placeholder="`最多可发出 ${availableShip}`"
          :rules="[{ required: true, message: '请输入发出数量' }]"
        >
          <template #button>
            <van-button size="small" type="success" plain :disabled="availableShip <= 0" @click.prevent="fillAll">
              一键填入全部可发出数量
            </van-button>
          </template>
        </van-field>
      </van-cell-group>

      <div v-if="availableShip <= 0" class="disabled-tip">
        <van-icon name="info-o" />
        <span>{{ shipUnavailableText }}</span>
      </div>

      <!-- 退件按钮 -->
      <div class="return-section">
        <div class="return-flow-tip">退件不打断主流程：正常发出优先，异常退件单独登记。</div>
        <van-button
          plain
          hairline
          type="warning"
          size="small"
          round
          icon="warning-o"
          @click="showReturnDialog = true"
        >
          退件
        </van-button>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <van-button
          round
          block
          type="primary"
          native-type="submit"
          :loading="submitting"
          :disabled="!shipCount || availableShip <= 0"
        >
          提交发出
        </van-button>
      </div>
    </van-form>

    <!-- 时间选择器 -->
    <van-popup v-model:show="showTimePicker" position="bottom">
      <van-datetime-picker
        v-model="currentDate"
        type="datetime"
        title="选择发出时间"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>

    <!-- 退件弹窗 -->
    <van-dialog
      v-model:show="showReturnDialog"
      title="退件信息"
      show-cancel-button
      :before-close="handleReturnBeforeClose"
    >
      <div class="return-form">
        <van-field
          v-model="returnReason"
          label="退件原因"
          placeholder="请输入退件原因"
          type="textarea"
          rows="2"
          autosize
        />
        <van-field
          v-model.number="returnCount"
          type="number"
          label="退件数量"
          placeholder="请输入退件数量"
        />
      </div>
    </van-dialog>

    <!-- 提交结果 -->
    <van-overlay :show="showResult">
      <div class="result-overlay" @click.stop>
        <van-icon
          :name="submitSuccess ? 'success' : 'cross'"
          :color="submitSuccess ? '#07c160' : '#ee0a24'"
          size="64"
        />
        <p class="result-message">{{ resultMessage }}</p>
        <van-button type="primary" round @click="handleResultConfirm">
          {{ submitSuccess ? '返回订单详情' : '确定' }}
        </van-button>
      </div>
    </van-overlay>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '@/stores/auth'
import { ship, getRecordDetail, returnGoods, type RecordInfo } from '@/api/records'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const record_id = computed(() => route.params.record_id as string)

const userInfo = computed(() => authStore.userInfo)

const orderInfo = ref<Partial<RecordInfo>>({
  record_id: '',
  order_id: '',
  process_id: '',
  factory_name: ''
})

const shipTime = ref('')
const currentDate = ref(new Date())
const shipCount = ref<number | undefined>()
const showTimePicker = ref(false)

const showReturnDialog = ref(false)
const returnReason = ref('')
const returnCount = ref<number | undefined>()

const submitting = ref(false)
const showResult = ref(false)
const submitSuccess = ref(false)
const resultMessage = ref('')

const minDate = new Date(2020, 0, 1)
const maxDate = new Date()

const nonNegative = (value: unknown) => Math.max(Number(value || 0), 0)
const clampQty = (value: unknown, maxValue: number) => Math.min(nonNegative(value), nonNegative(maxValue))
const currentReceiveQty = computed(() => nonNegative(orderInfo.value.current_receive_qty ?? orderInfo.value.total_receive_qty))
const currentShipQty = computed(() => clampQty(orderInfo.value.current_ship_qty ?? orderInfo.value.total_ship_qty ?? 0, currentReceiveQty.value))
const availableShip = computed(() => clampQty(orderInfo.value.available_ship_qty ?? (currentReceiveQty.value - currentShipQty.value), currentReceiveQty.value - currentShipQty.value))
const processTitle = computed(() => {
  const name = orderInfo.value.process_name || '工序'
  const seq = orderInfo.value.process_seq || orderInfo.value.process_id || '-'
  return `${seq} ${name}`
})
const shipUnavailableText = computed(() => {
  if (currentReceiveQty.value <= 0) return '本道尚未接收，不能发出'
  return '本道暂无可发出余量'
})

const goBack = () => {
  router.back()
}

const fillAll = () => {
  if (availableShip.value > 0) {
    shipCount.value = availableShip.value
  }
}

const onTimeConfirm = ({ selectedValues }: { selectedValues: (number | string)[] }) => {
  const [year, month, day, hour, minute] = selectedValues
  const date = new Date(year as number, (month as number) - 1, day as number, hour as number, minute as number)
  shipTime.value = date.toISOString().slice(0, 19).replace('T', ' ')
  showTimePicker.value = false
}

const handleReturnBeforeClose = async (action: string) => {
  if (action === 'confirm') {
    if (!returnReason.value.trim()) {
      showToast('请输入退件原因')
      return false
    }
    if (!returnCount.value || returnCount.value <= 0) {
      showToast('请输入有效的退件数量')
      return false
    }
    if (!orderInfo.value.previous_record_id) {
      showToast('首道工序无上道记录，不能退件')
      return false
    }
    try {
      submitting.value = true
      await returnGoods({
        from_record_id: orderInfo.value.previous_record_id,
        to_record_id: record_id.value,
        return_qty: returnCount.value,
        return_reason: returnReason.value.trim()
      })
      showToast('退件成功')
      returnReason.value = ''
      returnCount.value = undefined
      await loadOrderInfo()
      return true
    } catch (err) {
      console.error('退件失败:', err)
      showToast((err as any)?.response?.data?.detail || (err as any)?.response?.data?.message || '退件失败，请检查数量和权限')
      return false
    } finally {
      submitting.value = false
    }
  }
  return true
}

const loadOrderInfo = async () => {
  try {
    const res = await getRecordDetail(record_id.value)
    orderInfo.value = res
  } catch (err) {
    console.error('获取订单信息失败:', err)
    showToast('获取订单信息失败')
  }
}

const handleSubmit = async () => {
  if (availableShip.value <= 0) {
    showToast(shipUnavailableText.value)
    return
  }
  if (!shipTime.value) {
    showToast('请选择发出时间')
    return
  }
  if (!shipCount.value || shipCount.value <= 0) {
    showToast('请输入有效的发出数量')
    return
  }
  if (shipCount.value > availableShip.value) {
    showToast(`发出数量不能超过可发出量 ${availableShip.value}`)
    return
  }

  submitting.value = true
  try {
    await ship({
      record_id: record_id.value,
      ship_qty: shipCount.value,
      ship_time: shipTime.value
    })
    submitSuccess.value = true
    resultMessage.value = '发出成功'
    showResult.value = true
  } catch (err) {
    console.error('提交失败:', err)
    submitSuccess.value = false
    resultMessage.value = (err as any)?.response?.data?.detail || (err as any)?.response?.data?.message || '提交失败，请重试'
    showResult.value = true
  } finally {
    submitting.value = false
  }
}

const handleResultConfirm = () => {
  showResult.value = false
  if (submitSuccess.value) {
    const orderId = orderInfo.value.order_id
    router.replace(orderId ? `/kanban/${orderId}` : `/view/${record_id.value}`)
  }
}

onMounted(() => {
  // 设置默认发出时间为当前时间
  const now = new Date()
  currentDate.value = now
  shipTime.value = now.toISOString().slice(0, 19).replace('T', ' ')
  
  loadOrderInfo()
})
</script>

<style scoped>
.ship-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 20px;
}

.top-tip-card {
  margin: 12px 16px 0;
  padding: 16px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #07c160, #43d27d);
  box-shadow: 0 6px 16px rgba(7, 193, 96, 0.18);
}

.tip-label {
  font-size: 13px;
  opacity: 0.9;
}

.tip-num {
  margin-top: 4px;
  font-size: 34px;
  line-height: 38px;
  font-weight: 700;
}

.tip-desc {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.9;
}

.ship-form {
  margin-top: 12px;
}

.operation-guide-card {
  margin: 12px 16px 0;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e6f7ee;
}

.guide-title {
  color: #07c160;
  font-weight: 700;
  font-size: 15px;
}

.guide-desc {
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.guide-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 9px;
  color: #ff976a;
  font-size: 12px;
}

:deep(.highlight-value) {
  color: #07c160;
  font-weight: 700;
}

.disabled-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 16px 0;
  padding: 10px 12px;
  color: #ff976a;
  background: #fff7e8;
  border-radius: 8px;
  font-size: 13px;
}

.return-section {
  margin-top: 16px;
  padding: 0 16px;
  text-align: center;
}

.return-flow-tip {
  margin-bottom: 8px;
  color: #969799;
  font-size: 12px;
}

.return-form {
  padding: 16px;
}

.submit-section {
  margin-top: 24px;
  padding: 0 16px;
}

.result-overlay {
  background: white;
  border-radius: 12px;
  padding: 40px 32px;
  width: 280px;
  margin: 0 auto;
  margin-top: 50vh;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.result-message {
  font-size: 16px;
  color: #333;
  text-align: center;
}
</style>
