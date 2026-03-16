import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as svc from '@/services/caseService.js'

export const useRiskCaseStore = defineStore('riskCase', () => {
  // ── Case list ──
  const cases = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({
    page: 1, page_size: 20,
    farm_id: null, priority: null, current_status: null,
    case_type: null, assigned_expert_user_id: null, queue: null,
  })

  async function fetchCases() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.farm_id) params.farm_id = filters.value.farm_id
      if (filters.value.priority) params.priority = filters.value.priority
      if (filters.value.current_status) params.current_status = filters.value.current_status
      if (filters.value.case_type) params.case_type = filters.value.case_type
      if (filters.value.assigned_expert_user_id) params.assigned_expert_user_id = filters.value.assigned_expert_user_id
      if (filters.value.queue) params.queue = filters.value.queue

      const result = await svc.listCases(params)
      cases.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  // ── Queue ──
  const queueCases = ref([])
  const queueTotal = ref(0)
  const queueLoading = ref(false)
  const queuePage = ref(1)

  async function fetchQueue() {
    queueLoading.value = true
    try {
      const result = await svc.getQueueReview({ page: queuePage.value, page_size: 20 })
      queueCases.value = result.data
      queueTotal.value = result.meta.total
    } finally {
      queueLoading.value = false
    }
  }

  // ── Case detail ──
  const currentCase = ref(null)
  const timeline = ref([])
  const rcaRecords = ref([])

  async function fetchCase(id) {
    loading.value = true
    try {
      currentCase.value = await svc.getCase(id)
    } finally {
      loading.value = false
    }
  }

  async function fetchTimeline(caseId) {
    timeline.value = await svc.getTimeline(caseId)
  }

  async function fetchRcaRecords(caseId) {
    rcaRecords.value = await svc.listRcaRecords(caseId)
  }

  // ── Actions ──
  async function createCase(payload) {
    const created = await svc.createCase(payload)
    return created
  }

  async function updateCase(id, payload) {
    const updated = await svc.updateCase(id, payload)
    if (currentCase.value?.id === id) currentCase.value = updated
    return updated
  }

  async function assignExpert(caseId, expertUserId) {
    const updated = await svc.assignExpert(caseId, expertUserId)
    if (currentCase.value?.id === caseId) currentCase.value = updated
    return updated
  }

  async function changeStatus(caseId, targetStatus, version) {
    const updated = await svc.changeStatus(caseId, targetStatus, version)
    if (currentCase.value?.id === caseId) currentCase.value = updated
    return updated
  }

  // ── RCA actions ──
  async function createRcaRecord(caseId, payload) {
    const rca = await svc.createRcaRecord(caseId, payload)
    await fetchRcaRecords(caseId)
    return rca
  }

  async function updateRcaRecord(rcaId, payload) {
    const rca = await svc.updateRcaRecord(rcaId, payload)
    if (currentCase.value) await fetchRcaRecords(currentCase.value.id)
    return rca
  }

  async function approveRca(rcaId) {
    const rca = await svc.approveRca(rcaId)
    if (currentCase.value) await fetchRcaRecords(currentCase.value.id)
    return rca
  }

  async function createFactor(rcaId, payload) {
    const factor = await svc.createFactor(rcaId, payload)
    if (currentCase.value) await fetchRcaRecords(currentCase.value.id)
    return factor
  }

  async function updateFactor(factorId, payload) {
    const factor = await svc.updateFactor(factorId, payload)
    if (currentCase.value) await fetchRcaRecords(currentCase.value.id)
    return factor
  }

  async function deleteFactor(factorId) {
    await svc.deleteFactor(factorId)
    if (currentCase.value) await fetchRcaRecords(currentCase.value.id)
  }

  return {
    cases, totalRecords, loading, filters,
    fetchCases,
    queueCases, queueTotal, queueLoading, queuePage,
    fetchQueue,
    currentCase, timeline, rcaRecords,
    fetchCase, fetchTimeline, fetchRcaRecords,
    createCase, updateCase, assignExpert, changeStatus,
    createRcaRecord, updateRcaRecord, approveRca,
    createFactor, updateFactor, deleteFactor,
  }
})
