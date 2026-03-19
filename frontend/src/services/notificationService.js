import apiClient from '@/api/client.js'

export async function listNotifications(params = {}) {
  const { data } = await apiClient.get('/notifications', { params })
  return data // { data: [...], meta }
}

export async function getUnreadCount() {
  const { data } = await apiClient.get('/notifications/unread-count')
  return data.data.unread_count
}

export async function markRead(notificationId) {
  const { data } = await apiClient.post(`/notifications/${notificationId}/read`)
  return data.data
}

export async function bulkMarkRead(notificationIds) {
  const { data } = await apiClient.post('/notifications/bulk-read', {
    notification_ids: notificationIds,
  })
  return data.data.updated_count
}
