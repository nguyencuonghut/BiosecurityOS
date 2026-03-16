import apiClient from '@/api/client.js'

export async function listTrustScores(params = {}) {
  const { data } = await apiClient.get('/trust-scores', { params })
  return data // { data: [...], meta }
}

export async function calculateTrustScore(payload) {
  const { data } = await apiClient.post('/trust-scores/calculate', payload)
  return data.data
}

export async function getLatestTrustScore(farmId) {
  const { data } = await apiClient.get(`/trust-scores/farms/${farmId}/latest`)
  return data.data
}
