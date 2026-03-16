import apiClient from '@/api/client.js'

/**
 * Auth service — handles API calls for authentication.
 * Flow: Store → Service → API client
 */

export async function login(username, password) {
  const { data } = await apiClient.post('/auth/login', { username, password })
  return data // { access_token, refresh_token, token_type, expires_in }
}

export async function refreshToken(refreshTokenValue) {
  const { data } = await apiClient.post('/auth/refresh', {
    refresh_token: refreshTokenValue,
  })
  return data // { access_token, refresh_token, token_type, expires_in }
}

export async function logout(refreshTokenValue) {
  await apiClient.post('/auth/logout', {
    refresh_token: refreshTokenValue,
  })
}

export async function getMe() {
  const { data } = await apiClient.get('/auth/me')
  return data // { user, roles, permissions }
}
