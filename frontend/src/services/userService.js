import apiClient from '@/api/client.js'

// ── User CRUD ──────────────────────────────────────────────────

export async function listUsers(params = {}) {
  const { data } = await apiClient.get('/users', { params })
  return data // { data: [...], meta: { page, page_size, total, total_pages } }
}

export async function getUser(id) {
  const { data } = await apiClient.get(`/users/${id}`)
  return data.data
}

export async function createUser(payload) {
  const { data } = await apiClient.post('/users', payload)
  return data.data
}

export async function updateUser(id, payload) {
  const { data } = await apiClient.patch(`/users/${id}`, payload)
  return data.data
}

// ── Roles (reference data) ─────────────────────────────────────

export async function listRoles() {
  const { data } = await apiClient.get('/users/roles')
  return data.data
}

// ── Role assignment ────────────────────────────────────────────

export async function assignRole(userId, payload) {
  const { data } = await apiClient.post(`/users/${userId}/roles`, payload)
  return data.data
}

export async function removeRole(userId, userRoleId) {
  await apiClient.delete(`/users/${userId}/roles/${userRoleId}`)
}
