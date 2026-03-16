import apiClient from '@/api/client.js'

// ── Template CRUD ──────────────────────────────────────────────

export async function listTemplates(params = {}) {
  const { data } = await apiClient.get('/scorecard-templates', { params })
  return data // { data: [...], meta: {...} }
}

export async function getTemplate(id) {
  const { data } = await apiClient.get(`/scorecard-templates/${id}`)
  return data.data
}

export async function createTemplate(payload) {
  const { data } = await apiClient.post('/scorecard-templates', payload)
  return data.data
}

export async function updateTemplate(id, payload) {
  const { data } = await apiClient.patch(`/scorecard-templates/${id}`, payload)
  return data.data
}

export async function activateTemplate(id) {
  const { data } = await apiClient.post(`/scorecard-templates/${id}/activate`)
  return data.data
}

export async function archiveTemplate(id) {
  const { data } = await apiClient.post(`/scorecard-templates/${id}/archive`)
  return data.data
}

// ── Section CRUD ───────────────────────────────────────────────

export async function listSections(templateId) {
  const { data } = await apiClient.get(`/scorecard-templates/${templateId}/sections`)
  return data.data
}

export async function createSection(templateId, payload) {
  const { data } = await apiClient.post(`/scorecard-templates/${templateId}/sections`, payload)
  return data.data
}

export async function updateSection(sectionId, payload) {
  const { data } = await apiClient.patch(`/scorecard-sections/${sectionId}`, payload)
  return data.data
}

// ── Item CRUD ──────────────────────────────────────────────────

export async function listItems(sectionId) {
  const { data } = await apiClient.get(`/scorecard-sections/${sectionId}/items`)
  return data.data
}

export async function createItem(sectionId, payload) {
  const { data } = await apiClient.post(`/scorecard-sections/${sectionId}/items`, payload)
  return data.data
}

export async function updateItem(itemId, payload) {
  const { data } = await apiClient.patch(`/scorecard-items/${itemId}`, payload)
  return data.data
}

export async function deleteItem(itemId) {
  await apiClient.delete(`/scorecard-items/${itemId}`)
}
