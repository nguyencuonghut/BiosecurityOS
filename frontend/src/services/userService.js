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

export async function getRole(roleId) {
  const { data } = await apiClient.get(`/users/roles/${roleId}`)
  return data.data // { id, code, name, scope_type, description, permission_ids: [...] }
}

// ── Permissions (reference data) ──────────────────────────────

export async function listPermissions() {
  const { data } = await apiClient.get('/users/permissions')
  return data.data // [{ id, code, name, module, action }, ...]
}

// ── Role-Permission assignment ─────────────────────────────────

export async function assignPermissionToRole(roleId, permissionId) {
  const { data } = await apiClient.post(`/users/roles/${roleId}/permissions/${permissionId}`)
  return data.data
}

export async function revokePermissionFromRole(roleId, permissionId) {
  await apiClient.delete(`/users/roles/${roleId}/permissions/${permissionId}`)
}

// ── Role assignment (user ↔ role) ──────────────────────────────

export async function assignRole(userId, payload) {
  const { data } = await apiClient.post(`/users/${userId}/roles`, payload)
  return data.data
}

export async function removeRole(userId, userRoleId) {
  await apiClient.delete(`/users/${userId}/roles/${userRoleId}`)
}

