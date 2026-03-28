import apiClient from '@/api/client.js'

// ── Farm CRUD ──────────────────────────────────────────────────

export async function listFarms(params = {}) {
  const { data } = await apiClient.get('/farms', { params })
  return data // { data: [...], meta: { page, page_size, total, total_pages } }
}

export async function getFarm(id) {
  const { data } = await apiClient.get(`/farms/${id}`)
  return data.data
}

export async function createFarm(payload) {
  const { data } = await apiClient.post('/farms', payload)
  return data.data
}

export async function updateFarm(id, payload) {
  const { data } = await apiClient.patch(`/farms/${id}`, payload)
  return data.data
}

// ── Area Types ─────────────────────────────────────────────────

export async function listAreaTypes() {
  const { data } = await apiClient.get('/farms/area-types')
  return data.data
}

export async function createAreaType(payload) {
  const { data } = await apiClient.post('/farms/area-types', payload)
  return data.data
}

export async function updateAreaType(id, payload) {
  const { data } = await apiClient.put(`/farms/area-types/${id}`, payload)
  return data.data
}

export async function deleteAreaType(id) {
  await apiClient.delete(`/farms/area-types/${id}`)
}

// ── Area ───────────────────────────────────────────────────────

export async function listAreas(farmId) {
  const { data } = await apiClient.get(`/farms/${farmId}/areas`)
  return data.data
}

export async function createArea(farmId, payload) {
  const { data } = await apiClient.post(`/farms/${farmId}/areas`, payload)
  return data.data
}

export async function updateArea(farmId, areaId, payload) {
  const { data } = await apiClient.patch(`/farms/${farmId}/areas/${areaId}`, payload)
  return data.data
}

// ── Route ──────────────────────────────────────────────────────

export async function listRoutes(farmId) {
  const { data } = await apiClient.get(`/farms/${farmId}/routes`)
  return data.data
}

export async function createRoute(farmId, payload) {
  const { data } = await apiClient.post(`/farms/${farmId}/routes`, payload)
  return data.data
}

// ── External Risk Point ────────────────────────────────────────

export async function listRiskPoints(farmId) {
  const { data } = await apiClient.get(`/farms/${farmId}/external-risk-points`)
  return data.data
}

export async function createRiskPoint(farmId, payload) {
  const { data } = await apiClient.post(`/farms/${farmId}/external-risk-points`, payload)
  return data.data
}
