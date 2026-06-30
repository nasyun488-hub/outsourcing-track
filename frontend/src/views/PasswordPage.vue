<template>
  <div class="password-page">
    <!-- 顶部导航 -->
    <nav class="top-nav">
      <div class="nav-left">
        <button class="back-btn" @click="goBack">
          <i class="icon">←</i>
        </button>
        <h1 class="page-title">修改密码</h1>
      </div>
    </nav>

    <div class="content">
      <!-- 密码表单 -->
      <div class="form-section">
        <div class="form-group">
          <label class="form-label">当前密码</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="formData.oldPassword" 
            placeholder="请输入当前密码"
            :type="showOldPassword ? 'text' : 'password'"
          />
          <button class="eye-btn" @click="showOldPassword = !showOldPassword">
            {{ showOldPassword ? '🙈' : '👁️' }}
          </button>
        </div>

        <div class="form-group">
          <label class="form-label">新密码</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="formData.newPassword" 
            placeholder="请输入6-20位新密码"
            :type="showNewPassword ? 'text' : 'password'"
          />
          <button class="eye-btn" @click="showNewPassword = !showNewPassword">
            {{ showNewPassword ? '🙈' : '👁️' }}
          </button>
        </div>

        <div class="form-group">
          <label class="form-label">确认新密码</label>
          <input 
            type="password" 
            class="form-input" 
            v-model="formData.confirmPassword" 
            placeholder="请再次输入新密码"
            :type="showConfirmPassword ? 'text' : 'password'"
          />
          <button class="eye-btn" @click="showConfirmPassword = !showConfirmPassword">
            {{ showConfirmPassword ? '🙈' : '👁️' }}
          </button>
        </div>
      </div>

      <!-- 密码强度提示 -->
      <div class="strength-section" v-if="formData.newPassword">
        <div class="strength-label">密码强度</div>
        <div class="strength-bars">
          <div 
            class="strength-bar" 
            :class="getStrengthClass(1)"
          ></div>
          <div 
            class="strength-bar" 
            :class="getStrengthClass(2)"
          ></div>
          <div 
            class="strength-bar" 
            :class="getStrengthClass(3)"
          ></div>
        </div>
        <div class="strength-text">{{ strengthText }}</div>
      </div>

      <!-- 密码规则 -->
      <div class="rules-section">
        <div class="rules-title">密码规则</div>
        <ul class="rules-list">
          <li :class="passwordRules.length.valid">长度 6-20 位</li>
          <li :class="passwordRules.number.valid">包含数字</li>
          <li :class="passwordRules.letter.valid">包含字母</li>
          <li :class="passwordRules.special.valid">可包含特殊字符（@#$%等）</li>
        </ul>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <button 
          class="submit-btn" 
          @click="changePassword" 
          :disabled="submitting || !canSubmit"
        >
          {{ submitting ? '提交中...' : '确认修改' }}
        </button>
      </div>

      <!-- 忘记密码 -->
      <div class="forgot-section">
        <button class="forgot-btn" @click="forgotPassword">忘记密码？联系管理员重置</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const submitting = ref(false)

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const formData = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = computed(() => {
  const pwd = formData.value.newPassword
  return {
    length: {
      valid: pwd.length >= 6 && pwd.length <= 20 ? 'valid' : ''
    },
    number: {
      valid: /\d/.test(pwd) ? 'valid' : ''
    },
    letter: {
      valid: /[a-zA-Z]/.test(pwd) ? 'valid' : ''
    },
    special: {
      valid: /[!@#$%^&*()]/.test(pwd) || pwd.length === 0 ? 'valid' : ''
    }
  }
})

const strengthLevel = computed(() => {
  const pwd = formData.value.newPassword
  let level = 0
  if (pwd.length >= 6) level++
  if (/\d/.test(pwd) && /[a-zA-Z]/.test(pwd)) level++
  if (/[!@#$%^&*()]/.test(pwd) || pwd.length >= 12) level++
  return level
})

const strengthText = computed(() => {
  const texts = ['弱', '中', '强']
  return texts[strengthLevel.value - 1] || ''
})

const canSubmit = computed(() => {
  return formData.value.oldPassword &&
         formData.value.newPassword &&
         formData.value.confirmPassword &&
         formData.value.newPassword === formData.value.confirmPassword &&
         strengthLevel.value >= 1
})

const goBack = () => {
  router.back()
}

const getStrengthClass = (level: number) => {
  if (strengthLevel.value >= level) {
    return level === 1 ? 'weak' : level === 2 ? 'medium' : 'strong'
  }
  return ''
}

const changePassword = async () => {
  if (formData.value.newPassword !== formData.value.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }

  if (formData.value.newPassword.length < 6) {
    alert('密码长度至少6位')
    return
  }

  submitting.value = true
  try {
    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    alert('密码修改成功，请重新登录')
    formData.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    router.push('/login')
  } catch (e) {
    alert('修改失败，请检查当前密码是否正确')
  } finally {
    submitting.value = false
  }
}

const forgotPassword = () => {
  alert('请联系系统管理员进行密码重置')
}
</script>

<style scoped>
.password-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #ffffff;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e5e5;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn:hover {
  background: #f0f0f0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.content {
  padding: 16px;
  padding-bottom: 40px;
}

.form-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.form-group {
  padding: 16px 0;
  position: relative;
}

.form-group + .form-group {
  border-top: 1px solid #f0f0f0;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 44px 12px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
}

.eye-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
}

.strength-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.strength-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.strength-bars {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.strength-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  transition: background 0.2s;
}

.strength-bar.weak {
  background: #e74c3c;
}

.strength-bar.medium {
  background: #f39c12;
}

.strength-bar.strong {
  background: #27ae60;
}

.strength-text {
  font-size: 12px;
  color: #999;
  text-align: right;
}

.rules-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.rules-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.rules-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.rules-list li {
  font-size: 13px;
  color: #999;
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.rules-list li::before {
  content: '○';
  position: absolute;
  left: 0;
}

.rules-list li.valid {
  color: #27ae60;
}

.rules-list li.valid::before {
  content: '✓';
}

.submit-section {
  margin-bottom: 16px;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
}

.submit-btn:hover:not(:disabled) {
  background: #2980b9;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #ccc;
}

.forgot-section {
  text-align: center;
}

.forgot-btn {
  background: none;
  border: none;
  color: #3498db;
  font-size: 14px;
  cursor: pointer;
}

.forgot-btn:hover {
  text-decoration: underline;
}
</style>
