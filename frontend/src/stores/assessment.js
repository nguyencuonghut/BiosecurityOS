import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as assessmentService from '@/services/assessmentService.js'

export const useAssessmentStore = defineStore('assessment', () => {
  // ── List state ──
  const assessments = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({ page: 1, page_size: 20, farm_id: null, assessment_type: null, status: null })

  // ── Detail state ──
  const currentAssessment = ref(null)
  const spiderData = ref(null)

  // ── Actions ──
  async function fetchAssessments() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.farm_id) params.farm_id = filters.value.farm_id
      if (filters.value.assessment_type) params.assessment_type = filters.value.assessment_type
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.date_from) params.date_from = filters.value.date_from
      if (filters.value.date_to) params.date_to = filters.value.date_to

      const result = await assessmentService.listAssessments(params)
      assessments.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  async function fetchAssessment(id) {
    loading.value = true
    try {
      currentAssessment.value = await assessmentService.getAssessment(id)
    } finally {
      loading.value = false
    }
  }

  async function createAssessment(payload) {
    const created = await assessmentService.createAssessment(payload)
    currentAssessment.value = created
    return created
  }

  async function updateAssessment(id, payload) {
    currentAssessment.value = await assessmentService.updateAssessment(id, payload)
    return currentAssessment.value
  }

  async function bulkUpsertItems(assessmentId, items) {
    return await assessmentService.bulkUpsertItems(assessmentId, items)
  }

  async function submitAssessment(assessmentId) {
    const result = await assessmentService.submitAssessment(assessmentId)
    currentAssessment.value = result
    return result
  }

  async function changeStatus(assessmentId, status, version) {
    const result = await assessmentService.changeStatus(assessmentId, status, version)
    currentAssessment.value = result
    return result
  }

  async function fetchSpiderChart(assessmentId) {
    spiderData.value = await assessmentService.getSpiderChart(assessmentId)
    return spiderData.value
  }

  return {
    assessments, totalRecords, loading, filters,
    currentAssessment, spiderData,
    fetchAssessments, fetchAssessment,
    createAssessment, updateAssessment,
    bulkUpsertItems, submitAssessment, changeStatus,
    fetchSpiderChart,
  }
})
