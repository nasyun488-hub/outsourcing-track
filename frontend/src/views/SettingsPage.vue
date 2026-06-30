<template>
  <div class="settings-page">
    <div class="settings-hero">
      <div class="hero-title">设置中心</div>
      <div class="hero-subtitle">用户设置、账户管理、权限说明、密码修改</div>
      <button type="button" class="home-btn" @click="goHome">
        <van-icon name="home-o" />
        <span>回到主页</span>
      </button>
    </div>

    <div class="user-card">
      <div class="avatar">
        {{ currentUser?.username?.charAt(0) || currentUser?.name?.charAt(0) || 'U' }}
      </div>
      <div class="user-info">
        <div class="username">{{ currentUser?.name || currentUser?.username || '未登录' }}</div>
        <div class="role-label">当前登录用户 · {{ roleText }}</div>
      </div>
    </div>

    <section class="settings-section">
      <div class="section-title">用户设置</div>
      <van-cell-group inset>
        <van-cell title="深色模式" is-switch v-model="darkMode" />
        <van-cell title="通知提醒" is-switch v-model="notifyEnabled" />
      </van-cell-group>
    </section>

    <section class="settings-section">
      <div class="section-title">人员账户管理</div>
      <van-cell-group inset>
        <van-cell title="查看账户列表" is-link @click="goToUserManagement">
          <template #icon>
            <van-icon name="manager-o" size="20" />
          </template>
        </van-cell>
        <van-cell title="新建用户" is-link @click="goToUserManagement">
          <template #icon>
            <van-icon name="add-o" size="20" />
          </template>
        </van-cell>
      </van-cell-group>
    </section>

    <section class="settings-section">
      <div class="section-title">权限设置</div>
      <van-cell-group inset>
        <van-cell title="当前角色" :value="roleText">
          <template #icon>
            <van-icon name="shield-o" size="20" />
          </template>
        </van-cell>
        <van-cell title="权限说明" is-link @click="showPermissions">
          <template #icon>
            <van-icon name="info-o" size="20" />
          </template>
        </van-cell>
      </van-cell-group>
    </section>

    <section class="settings-section">
      <div class="section-title">密码管理</div>
      <van-cell-group inset>
        <van-cell title="修改密码" is-link @click="showPasswordModal">
          <template #icon>
            <van-icon name="lock" size="20" />
          </template>
        </van-cell>
      </van-cell-group>
    </section>

    <div class="action-buttons">
      <van-button type="primary" size="large" round block @click="saveSettings">保存设置</van-button>
      <van-button size="large" round block plain @click="logout">退出登录</van-button>
    </div>

    <van-dialog v-model:show="showPassword" title="修改密码" show-cancel-button @confirm="handleChangePassword">
      <van-form>
        <van-field v-model="passwordForm.old" type="password" label="当前密码" placeholder="请输入当前密码" />
        <van-field v-model="passwordForm.new" type="password" label="新密码" placeholder="请输入新密码" />
        <van-field v-model="passwordForm.confirm" type="password" label="确认密码" placeholder="请再次输入新密码" />
      </van-form>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const darkMode = ref(false)
const notifyEnabled = ref(true)
const showPassword = ref(false)

const passwordForm = reactive({
  old: '',
  new: '',
  confirm: ''
})

const currentUser = computed(() => authStore.userInfo || authStore.user)

const roleText = computed(() => {
  const roleMap: Record<string, string> = {
    enterprise_admin: '企业管理员',
    primary_admin: '主厂管理员',
    primary_operator: '主厂操作员',
    cooperative_admin: '协作厂管理员',
    cooperative_operator: '协作厂操作员',
    factory_admin: '厂家管理员',
    factory_operator: '厂家操作员',
    super_admin: '超级管理员',
    admin: '管理员',
    operator: '操作员',
    guest: '访客'
  }
  const role = currentUser.value?.role
  return role ? roleMap[role] || role : '未知角色'
})

const goHome = () => {
  router.push('/')
}

const goToUserManagement = () => {
  router.push('/admin/users')
}

const showPermissions = () => {
  router.push('/permissions')
}

const showPasswordModal = () => {
  showPassword.value = true
}

const handleChangePassword = () => {
  if (!passwordForm.old || !passwordForm.new || !passwordForm.confirm) {
    showToast('请填写完整密码信息')
    return
  }
  if (passwordForm.new !== passwordForm.confirm) {
    showToast('两次输入的密码不一致')
    return
  }
  showToast('密码修改成功')
  showPassword.value = false
  passwordForm.old = ''
  passwordForm.new = ''
  passwordForm.confirm = ''
}

const saveSettings = () => {
  showToast('设置已保存')
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  authStore.initFromStorage()
  darkMode.value = document.documentElement.classList.contains('dark')
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #f4f7fb;
  padding-bottom: 24px;
}

.settings-hero {
  padding: 18px 16px 28px;
  color: #fff;
  background: linear-gradient(135deg, #2f6bff 0%, #6d5dfc 58%, #8f63ff 100%);
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0 8px 24px rgba(47, 107, 255, 0.22);
}

.hero-title {
  font-size: 22px;
  font-weight: 900;
}

.hero-subtitle {
  margin-top: 5px;
  font-size: 12px;
  opacity: 0.9;
}

.home-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 999px;
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  font-size: 13px;
  cursor: pointer;
}

.home-btn:active {
  transform: scale(0.98);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: -16px 14px 16px;
  padding: 16px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(31, 45, 61, 0.08);
}

.avatar {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(135deg, #2f6bff, #7d63ff);
  font-size: 20px;
  font-weight: 800;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: 17px;
  font-weight: 700;
  color: #1f2d3d;
}

.role-label {
  margin-top: 3px;
  font-size: 12px;
  color: #7b8798;
}

.settings-section {
  margin: 0 14px 16px;
}

.section-title {
  margin-bottom: 8px;
  padding-left: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #7b8798;
}

.action-buttons {
  padding: 16px 14px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
