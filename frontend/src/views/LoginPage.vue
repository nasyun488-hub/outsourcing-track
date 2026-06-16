<template>
  <div class="login-page">
    <div class="login-shell">
      <div class="login-header">
        <div class="brand-mark">
          <van-icon name="scan" />
        </div>
        <h1>外协工序流转追踪｜扫码记录每一道流转</h1>
        <p>现场扫码接收、发出与异常留痕，手机上就能完成外协流转闭环。</p>
      </div>

      <div class="demo-tip">
        <div class="tip-title">
          <van-icon name="info-o" /> 演示环境提示
        </div>
        <div class="tip-text">如未接入短信服务，请使用管理员提供的演示手机号与验证码体验流程。</div>
      </div>

      <van-form @submit="handleLogin" class="login-form">
        <div class="form-title">手机号验证码登录</div>
        <van-cell-group inset>
          <van-field
            v-model="phone"
            type="tel"
            label="+86"
            placeholder="请输入手机号"
            clearable
            :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]"
          />
          <van-field
            v-model="code"
            type="digit"
            label="验证码"
            placeholder="请输入6位验证码"
            maxlength="6"
            clearable
            :error-message="codeError"
            :rules="[{ required: true, message: '请输入验证码' }]"
          >
            <template #button>
              <van-button
                size="small"
                type="primary"
                :disabled="countdown > 0"
                @click="handleSendCode"
                :loading="sending"
              >
                {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
              </van-button>
            </template>
          </van-field>
        </van-cell-group>

        <div class="helper-card">
          <div class="helper-title">收不到验证码？</div>
          <div class="helper-text">请确认手机号无误、短信未被拦截；验证码5分钟内有效，过期后请重新获取。</div>
        </div>

        <div class="login-button-wrapper">
          <van-button
            round
            block
            type="primary"
            native-type="submit"
            :loading="logging"
            :disabled="!phone || code.length !== 6"
          >
            登录并进入工作台
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const phone = ref('')
const code = ref('')
const codeError = ref('')
const countdown = ref(0)
const sending = ref(false)
const logging = ref(false)
const codeSentAt = ref<number | null>(null)

let countdownTimer: ReturnType<typeof setInterval> | null = null

const handleSendCode = async () => {
  if (countdown.value > 0) return

  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    showToast('请输入正确的手机号')
    return
  }

  codeError.value = ''
  sending.value = true
  try {
    const success = await authStore.sendCode(phone.value)
    if (success) {
      codeSentAt.value = Date.now()
      startCountdown()
      showToast('验证码已发送，请注意查收')
    }
  } finally {
    sending.value = false
  }
}

const startCountdown = () => {
  countdown.value = 60
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }
  }, 1000)
}

const handleLogin = async () => {
  codeError.value = ''
  if (code.value.length !== 6) {
    showToast('请输入6位验证码')
    return
  }

  if (codeSentAt.value && Date.now() - codeSentAt.value > 5 * 60 * 1000) {
    codeError.value = '验证码已过期，请重新获取'
    showToast('验证码已过期，请重新获取')
    return
  }

  logging.value = true
  try {
    const success = await authStore.login(phone.value, code.value)
    if (success) {
      router.replace('/')
    }
  } finally {
    logging.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(145deg, #1e63ff 0%, #5b6df7 46%, #8f63ff 100%);
  padding: 20px 16px;
  box-sizing: border-box;
}

.login-shell {
  min-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-header {
  color: white;
  margin-bottom: 18px;
}

.brand-mark {
  width: 54px;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  border-radius: 18px;
  font-size: 28px;
  color: #1e63ff;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 28px rgba(20, 48, 140, 0.18);
}

.login-header h1 {
  font-size: 25px;
  line-height: 1.25;
  margin: 0 0 10px;
  font-weight: 800;
}

.login-header p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  opacity: 0.9;
}

.demo-tip {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.26);
  border-radius: 16px;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
}

.tip-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
}

.tip-text {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.5;
  opacity: 0.9;
}

.login-form {
  background: white;
  border-radius: 20px;
  padding: 18px 0 20px;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.16);
}

.form-title {
  padding: 0 18px 12px;
  font-size: 17px;
  font-weight: 800;
  color: #202b3d;
}

.helper-card {
  margin: 12px 16px 0;
  padding: 11px 12px;
  border-radius: 14px;
  background: #f6f8fc;
}

.helper-title {
  font-size: 13px;
  font-weight: 700;
  color: #2f6bff;
}

.helper-text {
  margin-top: 5px;
  font-size: 12px;
  line-height: 1.5;
  color: #687386;
}

.login-button-wrapper {
  margin-top: 22px;
  padding: 0 16px;
}
</style>
