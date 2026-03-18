import apiClient from '@/api/client.js'

export async function getExecutiveSummary() {
  const { data } = await apiClient.get('/dashboards/executive-summary')
  return data.data
}

export async function getFarmDashboard(farmId) {
  const { data } = await apiClient.get(`/dashboards/farm/${farmId}`)
  return data.data
}

export async function getBenchmarkData(params = {}) {
  const { data } = await apiClient.get('/dashboards/benchmark', { params })
  return data.data
}

export async function getTrustGapsData() {
  const { data } = await apiClient.get('/dashboards/trust-gaps')
  return data.data
}

export async function getKillerMetricsTrendData(params = {}) {
  const { data } = await apiClient.get('/dashboards/killer-metrics-trend', { params })
  return data.data
}

export async function getScarHotspotsData(params = {}) {
  const { data } = await apiClient.get('/dashboards/scar-hotspots', { params })
  return data.data
}
