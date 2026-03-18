import apiClient from '@/api/client.js'

// ── Scar CRUD ──────────────────────────────────────────────────

export async function listScars(params = {}) {
  const { data } = await apiClient.get('/scars', { params })
  return data // { data: [...], meta }
}

export async function getScar(scarId) {
  const { data } = await apiClient.get(`/scars/${scarId}`)
  return data.data
}

export async function createScar(payload) {
  const { data } = await apiClient.post('/scars', payload)
  return data.data
}

export async function updateScar(scarId, payload) {
  const { data } = await apiClient.patch(`/scars/${scarId}`, payload)
  return data.data
}

// ── Validate ───────────────────────────────────────────────────

export async function validateScar(scarId) {
  const { data } = await apiClient.post(`/scars/${scarId}/validate`)
  return data.data
}

// ── Links ──────────────────────────────────────────────────────

export async function addScarLink(scarId, payload) {
  const { data } = await apiClient.post(`/scars/${scarId}/links`, payload)
  return data.data
}

// ── Scar Map ───────────────────────────────────────────────────

export async function getScarMap(farmId, params = {}) {
  const { data } = await apiClient.get(`/farms/${farmId}/scar-map`, { params })
  return data.data
}
