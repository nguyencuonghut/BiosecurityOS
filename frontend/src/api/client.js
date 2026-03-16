import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Token accessor — set by authStore on init ──
let _getTokens = () => ({
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
})
let _onTokenRefreshed = null // (accessToken, refreshToken) => void
let _onAuthFailed = null // () => void

export function setTokenCallbacks({ getTokens, onTokenRefreshed, onAuthFailed }) {
  if (getTokens) _getTokens = getTokens
  if (onTokenRefreshed) _onTokenRefreshed = onTokenRefreshed
  if (onAuthFailed) _onAuthFailed = onAuthFailed
}

// ── Request interceptor: attach Bearer token ──
apiClient.interceptors.request.use((config) => {
  const { accessToken } = _getTokens()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// ── Response interceptor: auto refresh on 401 ──
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { refreshToken } = _getTokens()
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const { data } = await axios.post(
          `${apiClient.defaults.baseURL}/auth/refresh`,
          { refresh_token: refreshToken },
        )

        // Backend returns flat: { access_token, refresh_token, token_type, expires_in }
        if (_onTokenRefreshed) {
          _onTokenRefreshed(data.access_token, data.refresh_token)
        }

        processQueue(null, data.access_token)

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        if (_onAuthFailed) {
          _onAuthFailed()
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient
