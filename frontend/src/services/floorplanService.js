import apiClient from '@/api/client.js'

// ── Floorplan Version ──────────────────────────────────────────

export async function listFloorplans(farmId) {
  const { data } = await apiClient.get(`/farms/${farmId}/floorplans`)
  return data.data
}

export async function getFloorplan(floorplanId) {
  const { data } = await apiClient.get(`/floorplans/${floorplanId}`)
  return data.data
}

export async function createFloorplan(farmId, payload) {
  const { data } = await apiClient.post(`/farms/${farmId}/floorplans`, payload)
  return data.data
}

export async function updateFloorplan(floorplanId, payload) {
  const { data } = await apiClient.patch(`/floorplans/${floorplanId}`, payload)
  return data.data
}

export async function approveFloorplan(floorplanId) {
  const { data } = await apiClient.post(`/floorplans/${floorplanId}/approve`)
  return data.data
}

// ── Markers ────────────────────────────────────────────────────

export async function listMarkers(floorplanId) {
  const { data } = await apiClient.get(`/floorplans/${floorplanId}/markers`)
  return data.data
}

export async function createMarker(floorplanId, payload) {
  const { data } = await apiClient.post(`/floorplans/${floorplanId}/markers`, payload)
  return data.data
}

export async function updateMarker(floorplanId, markerId, payload) {
  const { data } = await apiClient.patch(`/floorplans/${floorplanId}/markers/${markerId}`, payload)
  return data.data
}

export async function deleteMarker(floorplanId, markerId) {
  await apiClient.delete(`/floorplans/${floorplanId}/markers/${markerId}`)
}
