import apiClient from '@/api/client.js'

export async function listReports(params = {}) {
  const { data } = await apiClient.get('/reports', { params })
  return data
}

export async function createReport(payload) {
  const { data } = await apiClient.post('/reports', payload)
  return data.data
}

export async function getReport(reportId) {
  const { data } = await apiClient.get(`/reports/${reportId}`)
  return data.data
}

export async function downloadReport(reportId) {
  const response = await apiClient.get(`/reports/${reportId}/download`, {
    responseType: 'blob',
  })
  return response
}

export function getDownloadUrl(reportId) {
  const baseURL = apiClient.defaults.baseURL
  return `${baseURL}/reports/${reportId}/download`
}
