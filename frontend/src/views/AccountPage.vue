<template>
  <div class="account-page">
    <!-- 顶部导航 -->
    <nav class="top-nav">
      <div class="nav-left">
        <button class="back-btn" @click="goBack">
          <i class="icon">←</i>
        </button>
        <h1 class="page-title">账户管理</h1>
      </div>
      <div class="nav-right">
        <button class="save-btn" @click="saveProfile" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </nav>

    <div class="content">
      <!-- 头像区域 -->
      <div class="avatar-section">
        <div class="avatar">
          {{ currentUser?.username?.charAt(0) || 'U' }}
        </div>
        <button class="change-avatar-btn">更换头像</button>
      </div>

      <!-- 基本信息表单 -->
      <div class="form-section">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input 
            type="text" 
            class="form-input" 
            v-model="formData.username" 
            placeholder="请输入用户名"
          />
        </div>

        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input 
            type="email" 
            class="form-input" 
            v-model="formData.email" 
            placeholder="请输入邮箱"
          />
        </div>

        <div class="form-group">
          <label class="form-label">手机号</label>
          <input 
            type="tel" 
            class="form-input" 
            v-model="formData.phone" 
            placeholder="请输入手机号"
          />
        </div>

        <div class="form-group">
          <label class="form-label">所属工厂</label>
          <input 
            type="text" 
            class="form-input" 
            :value="factoryName" 
            disabled
          />
        </div>

        <div class="form-group">
          <label class="form-label">角色</label>
          <input 
            type="text" 
            class="form-input" 
            :value="roleText" 
            disabled
          />
        </div>

        <div class="form-group">
          <label class="form-label">注册时间</label>
          <input 
            type="text" 
            class="form-input" 
            :value="currentUser?.createdAt ? formatDate(currentUser.createdAt) : ''" 
            disabled
          />
        </div>
      </div>

      <!-- 操作提示 -->
      <div class="tip-section">
        <p class="tip-text">用户名、邮箱、手机号修改后需要重新登录生效</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)

const formData = ref({
  username: '',
  email: '',
  phone: ''
})

const currentUser = computed(() => authStore.user)

const factoryName = computed(() => {
  return currentUser.value?.factoryId ? '加载中...' : '未绑定工厂'
})

const roleText = computed(() => {
  const roleMap: Record<string, string> = {
    'super_admin': '超级管理员',
    'factory_admin': '工厂管理员',
    'factory_staff': '工厂员工',
    'external_factory': '外协厂家',
    'guest': '访客'
  }
  return roleMap[currentUser.value?.role] || currentUser.value?.role || ''
})

const goBack = () => {
  router.back()
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const saveProfile = async () => {
  if (!formData.value.username) {
    alert('用户名不能为空')
    return
  }

  saving.value = true
  try {
    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新本地用户信息
    const updatedUser = {
      ...currentUser.value,
      username: formData.value.username,
      email: formData.value.email,
      phone: formData.value.phone
    }
    authStore.setUser(updatedUser)
    
    alert('保存成功')
  } catch (e) {
    alert('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (currentUser.value) {
    formData.value = {
      username: currentUser.value.username || '',
      email: (currentUser.value as any).email || '',
      phone: (currentUser.value as any).phone || ''
    }
  }
})
</script>

<style scoped>
.account-page {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.save-btn {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.save-btn:hover:not(:disabled) {
  background: #2980b9;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content {
  padding: 16px;
  padding-bottom: 40px;
}

.avatar-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  font-size: 32px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.change-avatar-btn {
  padding: 8px 16px;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.change-avatar-btn:hover {
  background: #e5e5e5;
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
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  box-sizing: border-box;
}

.form-input:disabled {
  background: #f9f9f9;
  color: #999;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
}

.tip-section {
  padding: 16px;
}

.tip-text {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin: 0;
}
</style>
