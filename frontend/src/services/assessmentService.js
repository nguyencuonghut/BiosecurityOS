import apiClient from '@/api/client.js'

// ── Assessment CRUD ────────────────────────────────────────────

export async function listAssessments(params = {}) {
  const { data } = await apiClient.get('/assessments', { params })
  return data // { data: [...], meta: {...} }
}

export async function getAssessment(id) {
  const { data } = await apiClient.get(`/assessments/${id}`)
  return data.data
}

export async function createAssessment(payload) {
  const { data } = await apiClient.post('/assessments', payload)
  return data.data
}

export async function updateAssessment(id, payload) {
  const { data } = await apiClient.patch(`/assessments/${id}`, payload)
  return data.data
}

// ── Item Results ───────────────────────────────────────────────

export async function bulkUpsertItems(assessmentId, items) {
  const { data } = await apiClient.post(`/assessments/${assessmentId}/items/bulk-upsert`, { items })
  return data.data
}

// ── Submit ─────────────────────────────────────────────────────

export async function submitAssessment(assessmentId) {
  const { data } = await apiClient.post(`/assessments/${assessmentId}/submit`)
  return data.data
}

// ── State Machine ──────────────────────────────────────────────

export async function changeStatus(assessmentId, status, version) {
  const { data } = await apiClient.post(`/assessments/${assessmentId}/change-status`, { status, version })
  return data.data
}

// ── Spider Chart ───────────────────────────────────────────────

export async function getSpiderChart(assessmentId) {
  const { data } = await apiClient.get(`/assessments/${assessmentId}/spider-chart`)
  return data.data
}

// ── Attachments ────────────────────────────────────────────────

export async function addAttachment(assessmentId, payload) {
  const { data } = await apiClient.post(`/assessments/${assessmentId}/attachments`, payload)
  return data.data
}
