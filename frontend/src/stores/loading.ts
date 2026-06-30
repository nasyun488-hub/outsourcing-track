import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLoadingStore = defineStore('loading', () => {
  const isLoading = ref(false)
  const loadingText = ref('加载中...')

  function showLoading(text = '加载中...') {
    loadingText.value = text
    isLoading.value = true
  }

  function hideLoading() {
    isLoading.value = false
  }

  return {
    isLoading,
    loadingText,
    showLoading,
    hideLoading
  }
})
