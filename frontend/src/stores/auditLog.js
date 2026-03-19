import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as auditLogService from '@/services/auditLogService.js'

export const useAuditLogStore = defineStore('auditLog', () => {
  const logs = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({
    page: 1,
    page_size: 20,
    entity_type: null,
    actor_user_id: null,
    action: null,
    date_from: null,
    date_to: null,
  })

  async function fetchLogs() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.entity_type) params.entity_type = filters.value.entity_type
      if (filters.value.actor_user_id) params.actor_user_id = filters.value.actor_user_id
      if (filters.value.action) params.action = filters.value.action
      if (filters.value.date_from) params.date_from = filters.value.date_from
      if (filters.value.date_to) params.date_to = filters.value.date_to
      const res = await auditLogService.listAuditLogs(params)
      logs.value = res.data
      totalRecords.value = res.meta?.total || 0
    } catch (err) {
      console.error('Audit log store error:', err)
    } finally {
      loading.value = false
    }
  }

  function resetFilters() {
    filters.value = {
      page: 1, page_size: 20,
      entity_type: null, actor_user_id: null, action: null,
      date_from: null, date_to: null,
    }
  }

  return { logs, totalRecords, loading, filters, fetchLogs, resetFilters }
})
