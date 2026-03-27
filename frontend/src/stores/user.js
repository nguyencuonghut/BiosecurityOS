import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as userService from '@/services/userService.js'

export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({ page: 1, page_size: 20, status: null, region_id: null, farm_id: null, role: null })

  const currentUser = ref(null)

  // ── Role & Permission state ────────────────────────────────
  const roles = ref([])           // all roles (with permission_ids loaded)
  const permissions = ref([])     // all permissions (reference)
  const selectedRole = ref(null)  // currently selected role for the permission matrix

  async function fetchUsers() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.region_id) params.region_id = filters.value.region_id
      if (filters.value.farm_id) params.farm_id = filters.value.farm_id
      if (filters.value.role) params.role = filters.value.role
      if (filters.value.sort) params.sort = filters.value.sort

      const result = await userService.listUsers(params)
      users.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(id) {
    currentUser.value = await userService.getUser(id)
  }

  async function saveUser(payload, id = null) {
    if (id) {
      return await userService.updateUser(id, payload)
    }
    return await userService.createUser(payload)
  }

  async function assignRole(userId, payload) {
    return await userService.assignRole(userId, payload)
  }

  async function removeRole(userId, userRoleId) {
    await userService.removeRole(userId, userRoleId)
  }

  // ── Role Management ─────────────────────────────────────────

  async function fetchRoles() {
    const data = await userService.listRoles()
    roles.value = data
  }

  async function fetchRoleDetail(roleId) {
    const data = await userService.getRole(roleId)
    selectedRole.value = data
    return data
  }

  async function fetchPermissions() {
    const data = await userService.listPermissions()
    permissions.value = data
  }

  async function grantPermission(roleId, permissionId) {
    await userService.assignPermissionToRole(roleId, permissionId)
    // Update local state immediately (optimistic)
    if (selectedRole.value && selectedRole.value.id === roleId) {
      if (!selectedRole.value.permission_ids.includes(permissionId)) {
        selectedRole.value.permission_ids.push(permissionId)
      }
    }
  }

  async function revokePermission(roleId, permissionId) {
    await userService.revokePermissionFromRole(roleId, permissionId)
    // Update local state immediately (optimistic)
    if (selectedRole.value && selectedRole.value.id === roleId) {
      selectedRole.value.permission_ids = selectedRole.value.permission_ids.filter(
        (id) => id !== permissionId
      )
    }
  }

  return {
    users, totalRecords, loading, filters,
    currentUser,
    roles, permissions, selectedRole,
    fetchUsers, fetchUser, saveUser, assignRole, removeRole,
    fetchRoles, fetchRoleDetail, fetchPermissions, grantPermission, revokePermission,
  }
})

