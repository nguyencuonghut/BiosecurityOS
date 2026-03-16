import apiClient from '@/api/client.js'

export async function listRegions(params = {}) {
  const { data } = await apiClient.get('/regions', { params })
  return data // { data: [...], meta: { page, page_size, total, total_pages } }
}

export async function getRegion(id) {
  const { data } = await apiClient.get(`/regions/${id}`)
  return data.data
}

export async function createRegion(payload) {
  const { data } = await apiClient.post('/regions', payload)
  return data.data
}

export async function updateRegion(id, payload) {
  const { data } = await apiClient.patch(`/regions/${id}`, payload)
  return data.data
}
