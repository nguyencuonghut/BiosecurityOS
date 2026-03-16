import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as svc from '@/services/trustScoreService.js'

export const useTrustScoreStore = defineStore('trustScore', () => {
  const latestScore = ref(null)
  const loading = ref(false)

  async function fetchLatest(farmId) {
    loading.value = true
    try {
      latestScore.value = await svc.getLatestTrustScore(farmId)
    } catch (e) {
      // 404 = no trust score yet → that's okay
      if (e.response?.status === 404) {
        latestScore.value = null
      } else {
        throw e
      }
    } finally {
      loading.value = false
    }
  }

  async function calculate(payload) {
    loading.value = true
    try {
      const result = await svc.calculateTrustScore(payload)
      latestScore.value = result
      return result
    } finally {
      loading.value = false
    }
  }

  function $reset() {
    latestScore.value = null
    loading.value = false
  }

  return { latestScore, loading, fetchLatest, calculate, $reset }
})
