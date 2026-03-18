import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as dashboardService from '@/services/dashboardService.js'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const executive = ref(null)
  const benchmark = ref([])
  const trustGaps = ref([])
  const killerMetricsTrend = ref([])
  const scarHotspots = ref([])

  const loading = ref(false)
  const error = ref(null)

  // Computed
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)

  // Actions
  async function fetchExecutiveSummary() {
    try {
      executive.value = await dashboardService.getExecutiveSummary()
    } catch (err) {
      console.error('Dashboard store error:', err)
    }
  }

  async function fetchBenchmarkData(params) {
    try {
      benchmark.value = await dashboardService.getBenchmarkData(params)
    } catch (err) {
      console.error('Dashboard store error:', err)
    }
  }

  async function fetchTrustGapsData() {
    try {
      trustGaps.value = await dashboardService.getTrustGapsData()
    } catch (err) {
      console.error('Dashboard store error:', err)
    }
  }

  async function fetchKillerMetricsTrendData(params) {
    try {
      killerMetricsTrend.value = await dashboardService.getKillerMetricsTrendData(params)
    } catch (err) {
      console.error('Dashboard store error:', err)
    }
  }

  async function fetchScarHotspotsData(params) {
    try {
      scarHotspots.value = await dashboardService.getScarHotspotsData(params)
    } catch (err) {
      console.error('Dashboard store error:', err)
    }
  }

  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchExecutiveSummary(),
        fetchBenchmarkData(),
        fetchTrustGapsData(),
        fetchKillerMetricsTrendData(),
        fetchScarHotspotsData(),
      ])
    } catch (err) {
      error.value = err.message || 'Failed to fetch dashboard data'
    } finally {
      loading.value = false
    }
  }

  function clearDashboard() {
    executive.value = null
    benchmark.value = []
    trustGaps.value = []
    killerMetricsTrend.value = []
    scarHotspots.value = []
    error.value = null
  }

  return {
    executive,
    benchmark,
    trustGaps,
    killerMetricsTrend,
    scarHotspots,
    loading,
    error,
    isLoading,
    hasError,
    fetchExecutiveSummary,
    fetchBenchmarkData,
    fetchTrustGapsData,
    fetchKillerMetricsTrendData,
    fetchScarHotspotsData,
    fetchDashboard,
    clearDashboard,
  }
})
