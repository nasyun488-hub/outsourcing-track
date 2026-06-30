import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendSms, login as loginApi, passwordLogin as passwordLoginApi, fetchMe, type UserInfo } from '@/api/auth'
import { showToast } from 'vant'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string>('')

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

  const initFromStorage = () => {
    const storedToken = localStorage.getItem('token')
    const storedUserInfo = localStorage.getItem('userInfo')
    if (storedToken) {
      token.value = storedToken
    }
    if (storedUserInfo) {
      userInfo.value = JSON.parse(storedUserInfo)
    }
  }

  const sendCode = async (phone: string) => {
    try {
      const res = await sendSms(phone)
      showToast('验证码已发送' + (res.code ? '（' + res.code + '）' : ''))
      return res
    } catch {
      return null
    }
  }

  const login = async (phone: string, code: string) => {
    try {
      const res = await loginApi({ phone, code })
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      await fetchUserInfo()
      showToast('登录成功')
      return true
    } catch {
      return false
    }
  }

  const passwordLogin = async (account: string, password: string) => {
    try {
      const res = await passwordLoginApi({ account, password })
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      await fetchUserInfo()
      showToast('登录成功')
      return true
    } catch {
      return false
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push('/login')
    showToast('已退出登录')
  }

  const fetchUserInfo = async () => {
    try {
      const res = await fetchMe()
      userInfo.value = res as unknown as UserInfo
      localStorage.setItem('userInfo', JSON.stringify(res))
    } catch {
      // ignore
    }
  }

  const setUser = (user: UserInfo) => {
    userInfo.value = user
    localStorage.setItem('userInfo', JSON.stringify(user))
  }

  return {
    user: userInfo,
    userInfo,
    token,
    isLoggedIn,
    initFromStorage,
    sendCode,
    login,
    passwordLogin,
    logout,
    fetchUserInfo,
    setUser
  }
})
