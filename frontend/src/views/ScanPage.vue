<template>
  <div class="scan-page">
    <van-nav-bar title="扫码录入" left-arrow @click-left="goBack" />

    <div class="hero">
      <div class="hero-title">像超市收银一样连续扫码</div>
      <div class="hero-subtitle">支持真机扫码验收：连续扫码中，扫到码会自动加入下方清单；扫码枪、手机相机、拍照/相册都不会扫一个跳走，确认数量后统一提交。</div>
      <div class="hero-stats">
        <span>已扫数量 {{ scanCart.length }} 条</span>
        <span>可提交 {{ submittableCount }} 条</span>
        <span>异常 {{ failCount }} 条</span>
        <span>本次预计接收/发出总数 {{ estimatedReceiveQty }}/{{ estimatedShipQty }}</span>
      </div>
    </div>

    <van-tabs v-model:active="scanMethod" class="scan-tabs" @change="handleTabChange">
      <van-tab title="扫码枪" name="gun">
        <section class="panel">
          <van-field
            ref="gunInputRef"
            v-model="gunCode"
            label="扫码内容"
            placeholder="扫码枪扫入后自动回车，连续扫会逐条加入清单"
            clearable
            autocomplete="off"
            enterkeyhint="done"
            @keyup.enter="handleGunSubmit"
          />
          <div class="tip-card">
            <b>现场操作提示</b>
            <p>保持光标在输入框内，扫一件加一行；系统会默认带出可接收/可发出数量，操作员可直接改数量或删除行。</p>
          </div>
          <van-field
            v-model="manualCode"
            label="手工输入二维码编号"
            placeholder="扫码失败时，可手工输入二维码编号兜底"
            clearable
            autocomplete="off"
            enterkeyhint="done"
            @keyup.enter="handleManualSubmit"
          >
            <template #button>
              <van-button size="small" type="primary" :disabled="!manualCode.trim()" @click="handleManualSubmit">加入</van-button>
            </template>
          </van-field>
          <van-button
            type="primary"
            size="large"
            block
            round
            :loading="loading"
            :disabled="!gunCode.trim()"
            @click="handleGunSubmit"
          >
            加入录入清单
          </van-button>
        </section>
      </van-tab>

      <van-tab title="离线扫码导入" name="batch">
        <section class="panel">
          <van-field
            v-model="batchCodes"
            label="批量录入码值"
            placeholder="离线扫码导入：一行一个二维码；也支持逗号、空格、制表符分隔"
            type="textarea"
            rows="7"
            autosize
          />
          <div class="batch-actions">
            <van-button size="small" @click="batchCodes = demoBatch">填入示例</van-button>
            <van-button size="small" @click="clearBatch">清空</van-button>
          </div>
          <van-button
            type="primary"
            size="large"
            block
            round
            :loading="loading"
            :disabled="parsedBatchCodes.length === 0"
            @click="handleBatchSubmit"
          >
            加入清单 {{ parsedBatchCodes.length }} 条
          </van-button>
        </section>
      </van-tab>

      <van-tab title="手机扫码" name="camera">
        <section class="panel">
          <div v-if="!isCameraSecureContext" class="camera-secure-warning">
            手机摄像头需要 HTTPS 或 localhost；现场真机扫码验收请使用 https://&lt;局域网IP&gt;:8443/scan 访问，并允许浏览器摄像头权限。
          </div>
          <div class="camera-status-card">
            {{ cameraStatus }}
          </div>
          <div v-if="cameraErrorMessage" class="camera-error-card">
            {{ cameraErrorMessage }}
          </div>
          <div class="camera-container">
            <video
              ref="videoRef"
              class="camera-preview"
              autoplay
              muted
              playsinline
              v-show="cameraStarted"
            ></video>
            <div v-if="!cameraStarted" class="camera-placeholder">
              <van-icon name="scan" size="52" />
              <div>手机相机连续扫码</div>
              <small>识别成功后会加入下方清单，可继续对准下一张二维码。</small>
            </div>
            <div v-if="cameraStarted" class="scan-frame"><div class="scan-line"></div></div>
          </div>
          <div class="camera-actions">
            <van-button block round type="primary" @click="toggleCamera">
              {{ cameraStarted ? '关闭相机' : '打开相机连续扫码' }}
            </van-button>
            <van-button v-if="cameraStarted && !cameraPaused" block round @click="pauseCamera">暂停扫码</van-button>
            <van-button v-if="cameraStarted && cameraPaused" block round type="success" @click="resumeCamera">继续扫码</van-button>
            <van-button block round @click="triggerPhotoInput">拍照/相册识别</van-button>
          </div>
          <input
            ref="photoInputRef"
            class="photo-input"
            type="file"
            accept="image/*"
            capture="environment"
            @change="handlePhotoSelected"
          />
        </section>
      </van-tab>
    </van-tabs>

    <van-cell-group inset title="本次录入清单" class="cart">
      <div v-for="item in scanCart" :key="item.id" class="cart-row" :class="{ failed: item.status === 'fail', done: item.status === 'submitted', flash: item.id === flashId }">
        <div class="cart-row-main">
          <div class="cart-title">
            <span>{{ jumpTypeText(item.jump_type) }}</span>
            <van-tag v-if="item.source" plain type="primary">{{ sourceText(item.source) }}</van-tag>
            <van-tag v-if="item.status === 'submitted'" type="success">已提交</van-tag>
            <van-tag v-if="item.status === 'fail'" type="danger">不可提交</van-tag>
          </div>
          <div class="cart-code">{{ item.qr_code }}</div>
          <div class="cart-message">{{ item.message }}</div>
          <div v-if="item.record" class="cart-detail">
            工序：{{ item.record.process_name || item.record.process_id }}；可接收 {{ item.record.available_receive_qty ?? 0 }}，可发出 {{ item.record.available_ship_qty ?? 0 }}
          </div>
        </div>
        <div class="cart-row-side">
          <div v-if="isEditableItem(item)" class="qty-actions">
            <van-button size="mini" round plain @click="adjustQty(item, -1)">-</van-button>
            <van-button size="mini" round plain @click="adjustQty(item, 1)">+</van-button>
            <van-button size="mini" round plain @click="setQtyAll(item)">全部</van-button>
          </div>
          <van-field
            v-model.number="item.qty"
            class="qty-field"
            type="number"
            input-align="center"
            :disabled="!isEditableItem(item)"
            placeholder="数量"
            @blur="validateItemQty(item)"
          />
          <van-button v-if="item.status === 'fail'" size="small" type="primary" plain round @click="retryCartItem(item)">重试</van-button>
          <van-button icon="delete-o" size="small" type="danger" plain round @click="removeCartItem(item.id)" />
        </div>
      </div>
      <van-empty v-if="scanCart.length === 0" description="等待扫码加入清单" />
    </van-cell-group>

    <van-cell-group inset title="异常区" class="exception-section">
      <van-cell :title="`异常 ${exceptionItems.length} 条`" :value="showExceptions ? '收起异常' : '查看异常'" is-link @click="showExceptions = !showExceptions" />
      <template v-if="showExceptions">
        <div v-for="item in exceptionItems" :key="`exception-${item.id}`" class="exception-row">
          <div class="exception-main">
            <b>{{ item.qr_code }}</b>
            <span>{{ item.message }}</span>
          </div>
          <van-button size="small" type="primary" plain round @click="retryCartItem(item)">重试</van-button>
        </div>
        <van-empty v-if="exceptionItems.length === 0" description="暂无异常" />
      </template>
    </van-cell-group>

    <div class="submit-bar">
      <van-button block round type="primary" size="large" :loading="submitting" :disabled="submittableCount === 0" @click="submitCart">
        提交可录入记录 {{ submittableCount }} 条
      </van-button>
      <van-button block round plain size="small" :disabled="scanCart.length === 0 || submitting" @click="clearCompleted">
        清空已完成
      </van-button>
    </div>

    <van-overlay :show="loading || submitting">
      <div class="loading-wrapper">
        <van-loading size="48px">处理中...</van-loading>
      </div>
    </van-overlay>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { BrowserQRCodeReader, type IScannerControls } from '@zxing/browser'
import {
  getRecordDetail,
  receive,
  scanJudge,
  ship,
  type RecordInfo,
  type ScanJudgeResult
} from '@/api/records'

interface ScanCartItem {
  id: number
  qr_code: string
  source: 'gun' | 'batch' | 'camera' | 'photo'
  record_id?: string
  jump_type: ScanJudgeResult['jump_type']
  message: string
  qty: number
  maxQty: number
  status: 'ready' | 'fail' | 'submitting' | 'submitted'
  record?: RecordInfo
}

const router = useRouter()
const scanMethod = ref<'gun' | 'batch' | 'camera'>('gun')
const gunCode = ref('')
const manualCode = ref('')
const batchCodes = ref('')
const loading = ref(false)
const submitting = ref(false)
const cameraStarted = ref(false)
const cameraPaused = ref(false)
const cameraStatus = ref('未启动：请点击“打开相机连续扫码”，按浏览器提示允许摄像头权限。')
const cameraErrorMessage = ref('')
const gunInputRef = ref<any>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const photoInputRef = ref<HTMLInputElement | null>(null)
const scanCart = ref<ScanCartItem[]>([])
const showExceptions = ref(false)
const flashId = ref<number | null>(null)

let mediaStream: MediaStream | null = null
let qrReader: BrowserQRCodeReader | null = null
let scannerControls: IScannerControls | null = null
let flashTimer: ReturnType<typeof setTimeout> | null = null
const recentCameraTexts = new Map<string, number>()

const demoBatch = 'record_DEMO_PENDING_R1\nrecord_DEMO_RECEIVED_R1\nrecord_DEMO_SPLIT_R1'
const submittableCount = computed(() => scanCart.value.filter(canSubmitItem).length)
const failCount = computed(() => scanCart.value.filter(i => i.status === 'fail').length)
const exceptionItems = computed(() => scanCart.value.filter(i => i.status === 'fail'))
const estimatedReceiveQty = computed(() => scanCart.value.filter(i => i.jump_type === 'receive' && canSubmitItem(i)).reduce((sum, item) => sum + normalizeSubmitQty(item), 0))
const estimatedShipQty = computed(() => scanCart.value.filter(i => i.jump_type === 'ship' && canSubmitItem(i)).reduce((sum, item) => sum + normalizeSubmitQty(item), 0))
const parsedBatchCodes = computed(() => splitCodes(batchCodes.value).map(parseQRCode).filter(Boolean) as string[])
const isCameraSecureContext = computed(() => {
  if (typeof window === 'undefined') return true
  const hostname = window.location.hostname
  return window.isSecureContext || hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]'
})

function goBack() {
  router.back()
}

function focusGunInput() {
  nextTick(() => gunInputRef.value?.focus?.())
}

function handleTabChange(name: string | number) {
  if (name === 'gun') focusGunInput()
  if (name !== 'camera') stopCamera()
}

function splitCodes(content: string): string[] {
  return content
    .split(/[\n,，\t ]+/)
    .map(i => i.trim())
    .filter(Boolean)
}

function parseQRCode(content: string): string | null {
  const value = content.trim()
  if (!value) return null
  if (value.startsWith('record_') || value.startsWith('process_')) return value

  try {
    const parsed = JSON.parse(value)
    if (typeof parsed.qr_code === 'string' && parsed.qr_code.trim()) return parsed.qr_code.trim()
    if (typeof parsed.record_id === 'string' && parsed.record_id.trim()) return `record_${parsed.record_id.trim()}`
    if (typeof parsed.process_id === 'string' && typeof parsed.factory_id === 'string') {
      return `process_${parsed.process_id.trim()}_${parsed.factory_id.trim()}`
    }
  } catch {
    // 非 JSON 码值继续按无效处理
  }

  return null
}

function defaultQty(result: ScanJudgeResult, record?: RecordInfo): number {
  if (result.jump_type === 'receive') return positiveQty(record?.available_receive_qty)
  if (result.jump_type === 'ship') return positiveQty(record?.available_ship_qty)
  return 0
}

function positiveQty(value: unknown): number {
  if (value === undefined || value === null || value === '') return 1
  const qty = Number(value)
  return Number.isFinite(qty) && qty >= 0 ? qty : 1
}

function maxQtyFor(result: ScanJudgeResult, record?: RecordInfo): number {
  if (result.jump_type === 'receive') return Number(record?.available_receive_qty ?? 0)
  if (result.jump_type === 'ship') return Number(record?.available_ship_qty ?? 0)
  return 0
}

async function addScanToCart(qrCode: string, source: ScanCartItem['source']) {
  const duplicate = findDuplicateItem(qrCode)
  if (duplicate) {
    locateDuplicateItem(duplicate)
    return
  }

  loading.value = true
  try {
    const result = await scanJudge(qrCode)
    let record: RecordInfo | undefined
    if (result.record_id) {
      try {
        record = await getRecordDetail(result.record_id)
      } catch {
        // 详情失败不影响把扫码结果展示给操作员
      }
    }

    const item: ScanCartItem = {
      id: Date.now() + Math.random(),
      qr_code: qrCode,
      source,
      record_id: result.record_id,
      jump_type: result.jump_type,
      message: result.message,
      qty: defaultQty(result, record),
      maxQty: maxQtyFor(result, record),
      status: result.jump_type === 'receive' || result.jump_type === 'ship' ? 'ready' : 'fail',
      record
    }
    scanCart.value.unshift(item)
    vibrateFeedback()
    if (item.status === 'ready') {
      showToast(`已加入清单：${jumpTypeText(item.jump_type)} ${item.qty}`)
    } else {
      showExceptions.value = true
      showToast(result.message || '该码仅可查看，不能提交')
    }
  } catch (err) {
    const message = (err as any)?.response?.data?.detail || (err as any)?.response?.data?.message || '扫码解析失败'
    scanCart.value.unshift({
      id: Date.now() + Math.random(),
      qr_code: qrCode,
      source,
      jump_type: 'not_found',
      message,
      qty: 0,
      maxQty: 0,
      status: 'fail'
    })
    showExceptions.value = true
    vibrateFeedback([120, 80, 120])
    showToast(message)
  } finally {
    loading.value = false
  }
}

function findDuplicateItem(qrCode: string) {
  return scanCart.value.find(item => item.qr_code === qrCode)
}

function locateDuplicateItem(item: ScanCartItem) {
  flashId.value = item.id
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
    flashTimer = null
  }, 1400)
  vibrateFeedback([60, 40, 60])
  showToast('重复扫码，已定位到已有行')
}

function vibrateFeedback(pattern: VibratePattern = 50) {
  if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
    navigator.vibrate(pattern)
  }
}

async function handleGunSubmit() {
  const qrCode = parseQRCode(gunCode.value)
  if (!qrCode) {
    showToast('二维码格式不正确')
    return
  }
  gunCode.value = ''
  await addScanToCart(qrCode, 'gun')
  focusGunInput()
}

async function handleManualSubmit() {
  const qrCode = parseQRCode(manualCode.value)
  if (!qrCode) {
    showToast('二维码格式不正确')
    return
  }
  manualCode.value = ''
  await addScanToCart(qrCode, 'gun')
  focusGunInput()
}

async function handleBatchSubmit() {
  const codes = parsedBatchCodes.value
  if (codes.length === 0) {
    showToast('没有可解析的二维码')
    return
  }

  for (const qrCode of codes) {
    await addScanToCart(qrCode, 'batch')
  }
  batchCodes.value = ''
  showToast(`已加入清单 ${codes.length} 条`)
}

function clearBatch() {
  batchCodes.value = ''
}

function isEditableItem(item: ScanCartItem) {
  return (item.jump_type === 'receive' || item.jump_type === 'ship') && !!item.record_id && item.status === 'ready'
}

function canSubmitItem(item: ScanCartItem) {
  return isEditableItem(item) && Number(item.qty) > 0
}

function normalizeSubmitQty(item: ScanCartItem): number {
  const qty = Number(item.qty)
  if (!Number.isFinite(qty) || qty <= 0) return 0
  if (item.maxQty > 0) return Math.min(qty, item.maxQty)
  return qty
}

function overQtyMessage(item: ScanCartItem) {
  return item.jump_type === 'receive' ? '不能超过可接收' : '不能超过可发出'
}

function validateItemQty(item: ScanCartItem) {
  const qty = Number(item.qty)
  if (!Number.isFinite(qty) || qty <= 0) {
    item.qty = 0
    return
  }
  if (item.maxQty > 0 && qty > item.maxQty) {
    item.qty = item.maxQty
    showToast(overQtyMessage(item))
  }
}

function adjustQty(item: ScanCartItem, delta: number) {
  if (!isEditableItem(item)) return
  const nextQty = Math.max(0, Number(item.qty || 0) + delta)
  if (item.maxQty > 0 && nextQty > item.maxQty) {
    item.qty = item.maxQty
    showToast(overQtyMessage(item))
    return
  }
  item.qty = nextQty
}

function setQtyAll(item: ScanCartItem) {
  if (!isEditableItem(item)) return
  item.qty = item.maxQty > 0 ? item.maxQty : defaultQty({ jump_type: item.jump_type, message: item.message, record_id: item.record_id } as ScanJudgeResult, item.record)
}

async function submitCart() {
  const targets = scanCart.value.filter(canSubmitItem)
  if (targets.length === 0) {
    showToast('没有可提交的记录')
    return
  }

  submitting.value = true
  let success = 0
  let failed = 0
  for (const item of targets) {
    const qty = normalizeSubmitQty(item)
    if (!item.record_id || qty <= 0) continue
    item.status = 'submitting'
    try {
      if (item.jump_type === 'receive') {
        await receive({ record_id: item.record_id, receive_qty: qty })
      } else if (item.jump_type === 'ship') {
        await ship({ record_id: item.record_id, ship_qty: qty })
      }
      item.qty = qty
      item.status = 'submitted'
      item.message = '提交成功'
      success += 1
    } catch (err) {
      item.status = 'ready'
      item.message = (err as any)?.response?.data?.detail || (err as any)?.response?.data?.message || '提交失败，请重试'
      failed += 1
    }
  }
  submitting.value = false
  showToast(`提交完成：成功 ${success}，失败 ${failed}`)
}

function removeCartItem(id: number) {
  scanCart.value = scanCart.value.filter(item => item.id !== id)
}

function clearCompleted() {
  scanCart.value = scanCart.value.filter(item => item.status !== 'submitted')
}

async function retryCartItem(item: ScanCartItem) {
  const qrCode = item.qr_code
  const source = item.source
  removeCartItem(item.id)
  await addScanToCart(qrCode, source)
}

function jumpTypeText(type?: ScanJudgeResult['jump_type']) {
  return ({ receive: '接收', ship: '发出', view: '查看', not_found: '无效' } as Record<string, string>)[type || ''] || '-'
}

function sourceText(source: ScanCartItem['source']) {
  return ({ gun: '扫码枪', batch: '批量', camera: '相机', photo: '图片' } as Record<ScanCartItem['source'], string>)[source]
}

async function toggleCamera() {
  if (cameraStarted.value) {
    stopCamera()
    return
  }

  cameraErrorMessage.value = ''

  if (!isCameraSecureContext.value) {
    cameraErrorMessage.value = '当前页面不是安全上下文，手机浏览器会禁止摄像头；请使用 HTTPS 或 localhost 访问。'
    showToast('请使用 HTTPS 后再打开手机扫码')
    return
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    cameraErrorMessage.value = '当前浏览器不支持摄像头扫码，请更换 Chrome/Safari/微信内置浏览器，或使用拍照/相册识别。'
    showToast('浏览器不支持摄像头，请用图片识别兜底')
    return
  }

  try {
    if (!videoRef.value) return
    cameraStatus.value = '正在请求摄像头权限，请在浏览器地址栏允许摄像头权限。'
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    })
    videoRef.value.srcObject = mediaStream
    qrReader = qrReader || new BrowserQRCodeReader()
    scannerControls = await qrReader.decodeFromStream(
      mediaStream,
      videoRef.value,
      async (result) => {
        if (!result) return
        if (cameraPaused.value) return
        const text = result.getText()
        const qrCode = parseQRCode(text)
        if (!qrCode || isRecentCameraText(qrCode)) return
        await addScanToCart(qrCode, 'camera')
      }
    )
    cameraStarted.value = true
    cameraPaused.value = false
    cameraStatus.value = '相机已启动：对准二维码即可连续加入清单，不会自动跳页。'
    showToast('相机已启动，可连续扫码')
  } catch (err) {
    stopCamera()
    cameraErrorMessage.value = cameraErrorText(err)
    cameraStatus.value = '相机未启动：请按提示处理权限或使用拍照/相册兜底。'
    showToast('相机启动失败，请检查 HTTPS/浏览器权限/摄像头占用；可用拍照/相册识别')
  }
}

function pauseCamera() {
  cameraPaused.value = true
  cameraStatus.value = '已暂停扫码：相机画面保留，但不会继续加入清单。'
  showToast('已暂停扫码')
}

function resumeCamera() {
  cameraPaused.value = false
  cameraStatus.value = '相机已启动：对准二维码即可连续加入清单，不会自动跳页。'
  showToast('继续扫码')
}

function cameraErrorText(err: unknown) {
  const name = (err as DOMException)?.name || ''
  if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
    return '摄像头权限被拒绝：请在浏览器地址栏允许摄像头权限，或到系统设置中开启相机权限。'
  }
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
    return '未找到可用摄像头：请确认手机摄像头正常，或使用拍照/相册识别。'
  }
  if (name === 'NotReadableError' || name === 'TrackStartError') {
    return '摄像头被占用或无法读取：请关闭其它扫码/拍照应用后重试。'
  }
  if (name === 'OverconstrainedError' || name === 'ConstraintNotSatisfiedError') {
    return '后置摄像头参数不支持：请切换浏览器或使用拍照/相册识别。'
  }
  if (name === 'SecurityError') {
    return '浏览器安全策略阻止摄像头：请使用 HTTPS 地址访问扫码页。'
  }
  return '相机启动失败：请检查 HTTPS、浏览器权限、摄像头占用；也可以使用拍照/相册识别。'
}

function isRecentCameraText(qrCode: string): boolean {
  const now = Date.now()
  const last = recentCameraTexts.get(qrCode) || 0
  recentCameraTexts.set(qrCode, now)
  return now - last < 1800
}

function triggerPhotoInput() {
  photoInputRef.value?.click()
}

async function handlePhotoSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const imageUrl = URL.createObjectURL(file)
  loading.value = true
  try {
    qrReader = qrReader || new BrowserQRCodeReader()
    const decoded = await qrReader.decodeFromImageUrl(imageUrl)
    const qrCode = parseQRCode(decoded.getText())
    if (!qrCode) {
      showToast('图片中的二维码格式不正确')
      return
    }
    await addScanToCart(qrCode, 'photo')
  } catch {
    showToast('未识别到二维码，请重新拍照或选择清晰图片')
  } finally {
    loading.value = false
    URL.revokeObjectURL(imageUrl)
    input.value = ''
  }
}

function stopCamera() {
  if (scannerControls) {
    scannerControls.stop()
    scannerControls = null
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  if (videoRef.value) videoRef.value.srcObject = null
  cameraStarted.value = false
  cameraPaused.value = false
  cameraStatus.value = '未启动：请点击“打开相机连续扫码”，按浏览器提示允许摄像头权限。'
}

onMounted(focusGunInput)
onUnmounted(stopCamera)
</script>

<style scoped>
.scan-page {
  min-height: 100vh;
  padding-bottom: 120px;
  background: #f5f7fb;
}

.hero {
  margin: 12px;
  padding: 18px;
  border-radius: 18px;
  color: #fff;
  background: linear-gradient(135deg, #1677ff, #14c9c9);
  box-shadow: 0 8px 20px rgba(22, 119, 255, 0.18);
}

.hero-title {
  font-size: 20px;
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.92;
}

.hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.hero-stats span {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
}

.scan-tabs {
  background: transparent;
}

.panel {
  margin: 12px;
  padding: 14px;
  border-radius: 16px;
  background: #fff;
}

.tip-card {
  margin: 12px 0;
  padding: 12px;
  border-radius: 12px;
  color: #344054;
  background: #f2f7ff;
  font-size: 13px;
}

.tip-card p {
  margin: 6px 0 0;
  line-height: 1.5;
}

.batch-actions,
.camera-actions {
  display: flex;
  gap: 8px;
  margin: 10px 0 14px;
}

.camera-actions {
  flex-direction: column;
  margin-bottom: 0;
}

.camera-container {
  position: relative;
  width: 100%;
  height: 260px;
  overflow: hidden;
  border-radius: 16px;
  background: #101828;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-placeholder {
  color: #fff;
  text-align: center;
  line-height: 1.8;
}

.camera-placeholder small {
  color: rgba(255, 255, 255, 0.72);
}

.camera-secure-warning,
.camera-status-card,
.camera-error-card {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.camera-secure-warning {
  border: 1px solid #ffd591;
  color: #ad6800;
  background: #fff7e6;
}

.camera-status-card {
  border: 1px solid #91caff;
  color: #0958d9;
  background: #e6f4ff;
}

.camera-error-card {
  border: 1px solid #ffccc7;
  color: #cf1322;
  background: #fff1f0;
}

.scan-frame {
  position: absolute;
  width: 200px;
  height: 200px;
  border: 2px solid #00d5ff;
  border-radius: 16px;
  overflow: hidden;
  pointer-events: none;
}

.scan-line {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d5ff, transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { transform: translateY(0); }
  50% { transform: translateY(198px); }
  100% { transform: translateY(0); }
}

.photo-input {
  display: none;
}

.cart {
  margin-top: 16px;
  padding-bottom: 12px;
}

.cart-row {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid #eef0f5;
  background: #fff;
}

.cart-row:last-child {
  border-bottom: 0;
}

.cart-row-main {
  flex: 1;
  min-width: 0;
}

.cart-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  color: #1d2939;
}

.cart-code {
  margin-top: 6px;
  font-size: 13px;
  color: #344054;
  word-break: break-all;
}

.cart-message,
.cart-detail {
  margin-top: 4px;
  font-size: 12px;
  color: #667085;
  line-height: 1.4;
}

.cart-row-side {
  width: 112px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}

.qty-field {
  padding: 0;
  overflow: hidden;
  border: 1px solid #d0d5dd;
  border-radius: 10px;
}

.flash {
  animation: row-flash 1.4s ease-in-out;
}

@keyframes row-flash {
  0%, 100% { background: #fff; }
  20%, 70% { background: #fff7e6; }
}

.exception-section {
  margin-top: 12px;
}

.exception-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-top: 1px solid #eef0f5;
  background: #fff;
}

.exception-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  font-size: 12px;
  color: #667085;
}

.exception-main b {
  color: #1d2939;
  word-break: break-all;
}

.failed .cart-title,
.failed .cart-message {
  color: #ee0a24;
}

.done {
  opacity: 0.76;
}

.submit-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 -4px 18px rgba(16, 24, 40, 0.08);
}

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
