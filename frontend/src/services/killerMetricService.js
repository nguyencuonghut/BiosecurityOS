import apiClient from '@/api/client.js'

// ── Definitions ────────────────────────────────────────────────

export async function listDefinitions(params = {}) {
  const { data } = await apiClient.get('/killer-metric-definitions', { params })
  return data // { data: [...], meta }
}

export async function createDefinition(payload) {
  const { data } = await apiClient.post('/killer-metric-definitions', payload)
  return data.data
}

export async function updateDefinition(id, payload) {
  const { data } = await apiClient.patch(`/killer-metric-definitions/${id}`, payload)
  return data.data
}

// ── Events ─────────────────────────────────────────────────────

export async function listEvents(params = {}) {
  const { data } = await apiClient.get('/killer-metric-events', { params })
  return data // { data: [...], meta }
}

export async function getEvent(id) {
  const { data } = await apiClient.get(`/killer-metric-events/${id}`)
  return data.data
}

export async function createEvent(payload) {
  const { data } = await apiClient.post('/killer-metric-events', payload)
  return data.data
}

export async function updateEvent(id, payload) {
  const { data } = await apiClient.patch(`/killer-metric-events/${id}`, payload)
  return data.data
}
