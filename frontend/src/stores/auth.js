import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setTokenCallbacks } from '@/api/client.js'
import * as authService from '@/services/authService.js'
import router from '@/router/index.js'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(null)
  const roles = ref([])
  const permissions = ref([])
  const loading = ref(false)

  // ── Getters ──
  const isAuthenticated = computed(() => !!accessToken.value)
  const fullName = computed(() => user.value?.full_name || '')

  function hasPermission(perm) {
    return permissions.value.includes(perm)
  }

  function hasAnyPermission(perms) {
    return perms.some((p) => permissions.value.includes(p))
  }

  // ── Internal helpers ──
  function _persistTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function _clearAll() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    roles.value = []
    permissions.value = []
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // ── Wire up client.js callbacks ──
  setTokenCallbacks({
    getTokens: () => ({
      accessToken: accessToken.value,
      refreshToken: refreshToken.value,
    }),
    onTokenRefreshed: (newAccess, newRefresh) => {
      _persistTokens(newAccess, newRefresh)
    },
    onAuthFailed: () => {
      _clearAll()
      router.push({ name: 'Login' })
    },
  })

  // ── Actions ──
  async function login(username, password) {
    loading.value = true
    try {
      const data = await authService.login(username, password)
      _persistTokens(data.access_token, data.refresh_token)
      await fetchProfile()
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    const data = await authService.getMe()
    user.value = data.user
    roles.value = data.roles
    permissions.value = data.permissions
  }

  async function logout() {
    try {
      if (refreshToken.value) {
        await authService.logout(refreshToken.value)
      }
    } catch {
      // Ignore logout API errors — clear local state regardless
    } finally {
      _clearAll()
      router.push({ name: 'Login' })
    }
  }

  /**
   * Called once on app start — if tokens exist, fetch profile.
   * If fetch fails (expired/invalid), clear and redirect to login.
   */
  async function init() {
    if (!accessToken.value) return
    try {
      await fetchProfile()
    } catch {
      _clearAll()
    }
  }

  return {
    // state
    accessToken,
    refreshToken,
    user,
    roles,
    permissions,
    loading,
    // getters
    isAuthenticated,
    fullName,
    // methods
    hasPermission,
    hasAnyPermission,
    login,
    logout,
    fetchProfile,
    init,
  }
})
