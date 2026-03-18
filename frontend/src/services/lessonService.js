import apiClient from '@/api/client.js'

export async function listLessons(params = {}) {
  const { data } = await apiClient.get('/lessons', { params })
  return data // { data: [...], meta }
}

export async function getLesson(lessonId) {
  const { data } = await apiClient.get(`/lessons/${lessonId}`)
  return data.data
}

export async function createLesson(payload) {
  const { data } = await apiClient.post('/lessons', payload)
  return data.data
}

export async function updateLesson(lessonId, payload) {
  const { data } = await apiClient.patch(`/lessons/${lessonId}`, payload)
  return data.data
}

export async function validateLesson(lessonId) {
  const { data } = await apiClient.post(`/lessons/${lessonId}/validate`)
  return data.data
}

export async function addReference(lessonId, payload) {
  const { data } = await apiClient.post(`/lessons/${lessonId}/references`, payload)
  return data.data
}

export async function addTag(lessonId, payload) {
  const { data } = await apiClient.post(`/lessons/${lessonId}/tags`, payload)
  return data.data
}

export async function searchSimilar(params = {}) {
  const { data } = await apiClient.get('/lessons/search/similar', { params })
  return data // { data: [...], meta }
}
