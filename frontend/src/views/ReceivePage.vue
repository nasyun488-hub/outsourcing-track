<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="receive-page">
    <QuickNavStrip />
    <van-nav-bar
      title="接收操作台"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    />

    <div class="top-tip-card">
      <div class="tip-label">接收操作台｜本次可接收</div>
      <div class="tip-num">{{ availableReceive }}</div>
      <div class="tip-desc">少输入：核对上道已发与本道已收后，可一键填入全部可接收数量</div>
    </div>

    <div class="operation-guide-card">
      <div class="guide-title">本次可接收：{{ availableReceive }}</div>
      <div class="guide-desc">提交后返回订单详情，方便继续查看整单流转。</div>
      <div v-if="availableReceive <= 0" class="guide-warning">
        <van-icon name="warning-o" />
        <span>不可接收原因：{{ receiveUnavailableText }}</span>
      </div>
    </div>

    <van-form @submit="handleSubmit" class="receive-form">
      <!-- 只读信息 -->
      <van-cell-group inset title="订单信息">
        <van-cell title="订单号" :value="orderInfo.order_id || record_id" />
        <van-cell title="工序" :value="processTitle" />
        <van-cell title="厂家" :value="orderInfo.factory_name || '-'" />
        <van-cell title="上道已发" :value="`${prevShipQty}`" />
        <van-cell title="本道已收" :value="`${currentReceiveQty}`" />
        <van-cell title="本次可接收" :value="`${availableReceive}`" value-class="highlight-value" />
      </van-cell-group>

      <!-- 接收信息 -->
      <van-cell-group inset title="接收信息">
        <van-cell title="接收人" :value="userInfo?.name || '-'" />
        <van-field
          v-model="receiveTime"
          is-link
          readonly
          label="接收时间"
          placeholder="请选择接收时间"
          @click="showTimePicker = true"
        />
        <van-field
          v-model.number="receiveCount"
          type="number"
          label="接收数量"
          :placeholder="`最多可接收 ${availableReceive}`"
          :rules="[{ required: true, message: '请输入接收数量' }]"
        >
          <template #button>
            <van-button size="small" type="primary" plain :disabled="availableReceive <= 0" @click.prevent="fillAll">
              一键填入全部可接收数量
            </van-button>
          </template>
        </van-field>
      </van-cell-group>

      <div v-if="availableReceive <= 0" class="disabled-tip">
        <van-icon name="info-o" />
        <span>不可接收原因：{{ receiveUnavailableText }}</span>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <van-button
          round
          block
          type="primary"
          native-type="submit"
          :loading="submitting"
          :disabled="!receiveCount || availableReceive <= 0"
        >
          提交接收
        </van-button>
      </div>
    </van-form>

    <!-- 时间选择器 -->
    <van-popup v-model:show="showTimePicker" position="bottom">
      <van-datetime-picker
        v-model="currentDate"
        type="datetime"
        title="选择接收时间"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>

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
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useAuthStore } from '@/stores/auth'
import { getRecordDetail, receive } from '@/api/records'
import QuickNavStrip from '@/components/QuickNavStrip.vue'

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

const receiveTime = ref('')
const currentDate = ref(new Date())
const receiveCount = ref<number | undefined>()
const showTimePicker = ref(false)

const minDate = new Date(2020, 0, 1)
const maxDate = new Date()

const submitting = ref(false)
const showResult = ref(false)
const submitSuccess = ref(false)
const resultMessage = ref('')

const nonNegative = (value: unknown) => Math.max(Number(value || 0), 0)
const clampQty = (value: unknown, maxValue: number) => Math.min(nonNegative(value), nonNegative(maxValue))
const prevShipQty = computed(() => nonNegative(orderInfo.value.prev_ship_qty))
const currentReceiveQty = computed(() => clampQty(orderInfo.value.current_receive_qty ?? orderInfo.value.total_receive_qty ?? 0, prevShipQty.value))
const availableReceive = computed(() => clampQty(orderInfo.value.available_receive_qty ?? (prevShipQty.value - currentReceiveQty.value), prevShipQty.value - currentReceiveQty.value))
const processTitle = computed(() => {
  const name = orderInfo.value.process_name || '工序'
  const seq = orderInfo.value.process_seq || orderInfo.value.process_id || '-'
  return `${seq} ${name}`
})
const receiveUnavailableText = computed(() => {
  if (prevShipQty.value <= 0) return '暂无可接收数量，请等待上道工序发出'
  return '本道暂无可接收余量'
})

const goBack = () => {
  router.back()
}

const fillAll = () => {
  if (availableReceive.value > 0) {
    receiveCount.value = availableReceive.value
  }
}

const onTimeConfirm = ({ selectedValues }: { selectedValues: (number | string)[] }) => {
  const [year, month, day, hour, minute] = selectedValues
  const date = new Date(year as number, (month as number) - 1, day as number, hour as number, minute as number)
  receiveTime.value = date.toISOString().slice(0, 19).replace('T', ' ')
  showTimePicker.value = false
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
  if (availableReceive.value <= 0) {
    showToast(receiveUnavailableText.value)
    return
  }
  if (!receiveTime.value) {
    showToast('请选择接收时间')
    return
  }
  if (!receiveCount.value || receiveCount.value <= 0) {
    showToast('请输入有效的接收数量')
    return
  }

  if (receiveCount.value > availableReceive.value) {
    showToast(`接收数量不能超过可接收量 ${availableReceive.value}`)
    return
  }

  submitting.value = true
  try {
    await receive({
      record_id: record_id.value,
      receive_qty: receiveCount.value,
      receive_time: receiveTime.value
    })
    submitSuccess.value = true
    resultMessage.value = '接收成功'
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
  // 设置默认接收时间为当前时间
  const now = new Date()
  currentDate.value = now
  receiveTime.value = now.toISOString().slice(0, 19).replace('T', ' ')
  
  loadOrderInfo()
})
</script>

<style scoped>
.receive-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 20px;
}

.top-tip-card {
  margin: 12px 16px 0;
  padding: 16px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #1989fa, #4facfe);
  box-shadow: 0 6px 16px rgba(25, 137, 250, 0.18);
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

.receive-form {
  margin-top: 12px;
}

.operation-guide-card {
  margin: 12px 16px 0;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e8f3ff;
}

.guide-title {
  color: #1989fa;
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
  color: #1989fa;
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
