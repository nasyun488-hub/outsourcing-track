import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../api/kanban'

export interface Notification {
  notif_id: string
  title: string
  content: string
  created_at: string
  is_read: boolean
  related_id?: string
  related_type?: string
  jump_url?: string
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])
  const loading = ref(false)

  // 未读数
  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.is_read).length
  })

  // 获取通知列表
  async function fetchNotificationList() {
    loading.value = true
    try {
      const res = await fetchNotifications()
      // Normalize is_read from number/string/boolean (0/1) to boolean
      notifications.value = (res.items || []).map(n => ({
        ...n,
        content: n.content || '',
        is_read: n.is_read === true || n.is_read === 1 || n.is_read === '1'
      }))
    } finally {
      loading.value = false
    }
  }

  // 标记已读
  async function markAsRead(notif_id: string) {
    await markNotificationRead(notif_id)
    const notification = notifications.value.find(n => n.notif_id === notif_id)
    if (notification) {
      notification.is_read = true
    }
  }

  // 全部标记已读
  async function markAllAsRead() {
    await markAllNotificationsRead()
    notifications.value.forEach(n => {
      n.is_read = true
    })
  }

  return {
    notifications,
    loading,
    unreadCount,
    fetchNotificationList,
    markAsRead,
    markAllAsRead
  }
})
