import apiClient from '@/api/client.js'

// ── Cases ──────────────────────────────────────────────────────

export async function listCases(params = {}) {
  const { data } = await apiClient.get('/cases', { params })
  return data // { data: [...], meta }
}

export async function getCase(id) {
  const { data } = await apiClient.get(`/cases/${id}`)
  return data.data
}

export async function createCase(payload) {
  const { data } = await apiClient.post('/cases', payload)
  return data.data
}

export async function updateCase(id, payload) {
  const { data } = await apiClient.patch(`/cases/${id}`, payload)
  return data.data
}

export async function assignExpert(caseId, expertUserId) {
  const { data } = await apiClient.post(`/cases/${caseId}/assign-expert`, { expert_user_id: expertUserId })
  return data.data
}

export async function changeStatus(caseId, targetStatus, version) {
  const { data } = await apiClient.post(`/cases/${caseId}/change-status`, { target_status: targetStatus, version })
  return data.data
}

export async function getQueueReview(params = {}) {
  const { data } = await apiClient.get('/cases/queue/review', { params })
  return data // { data: [...], meta }
}

export async function getTimeline(caseId) {
  const { data } = await apiClient.get(`/cases/${caseId}/timeline`)
  return data.data
}

// ── RCA Records ────────────────────────────────────────────────

export async function listRcaRecords(caseId) {
  const { data } = await apiClient.get(`/cases/${caseId}/rca-records`)
  return data.data
}

export async function createRcaRecord(caseId, payload) {
  const { data } = await apiClient.post(`/cases/${caseId}/rca-records`, payload)
  return data.data
}

export async function getRcaRecord(rcaId) {
  const { data } = await apiClient.get(`/rca-records/${rcaId}`)
  return data.data
}

export async function updateRcaRecord(rcaId, payload) {
  const { data } = await apiClient.patch(`/rca-records/${rcaId}`, payload)
  return data.data
}

export async function approveRca(rcaId) {
  const { data } = await apiClient.post(`/rca-records/${rcaId}/approve`)
  return data.data
}

// ── RCA Factors ────────────────────────────────────────────────

export async function createFactor(rcaId, payload) {
  const { data } = await apiClient.post(`/rca-records/${rcaId}/factors`, payload)
  return data.data
}

export async function updateFactor(factorId, payload) {
  const { data } = await apiClient.patch(`/rca-factors/${factorId}`, payload)
  return data.data
}

export async function deleteFactor(factorId) {
  await apiClient.delete(`/rca-factors/${factorId}`)
}
