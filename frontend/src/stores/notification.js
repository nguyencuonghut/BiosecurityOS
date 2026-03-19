import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as notificationService from '@/services/notificationService.js'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const totalRecords = ref(0)
  const unreadCount = ref(0)
  const loading = ref(false)
  const filters = ref({ page: 1, page_size: 20, status: null })

  async function fetchNotifications() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.status) params.status = filters.value.status
      const res = await notificationService.listNotifications(params)
      notifications.value = res.data
      totalRecords.value = res.meta?.total || 0
    } catch (err) {
      console.error('Notification store error:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    try {
      unreadCount.value = await notificationService.getUnreadCount()
    } catch (err) {
      console.error('Unread count error:', err)
    }
  }

  async function markAsRead(notificationId) {
    await notificationService.markRead(notificationId)
    const item = notifications.value.find((n) => n.id === notificationId)
    if (item) {
      item.read_at = new Date().toISOString()
      item.status = 'read'
    }
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function bulkMarkAsRead(ids) {
    const count = await notificationService.bulkMarkRead(ids)
    ids.forEach((id) => {
      const item = notifications.value.find((n) => n.id === id)
      if (item) {
        item.read_at = new Date().toISOString()
        item.status = 'read'
      }
    })
    unreadCount.value = Math.max(0, unreadCount.value - count)
    return count
  }

  return {
    notifications, totalRecords, unreadCount, loading, filters,
    fetchNotifications, fetchUnreadCount, markAsRead, bulkMarkAsRead,
  }
})
