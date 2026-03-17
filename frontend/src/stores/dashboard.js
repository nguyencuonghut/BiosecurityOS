import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dashboardService from '@/services/dashboardService'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const executive = ref(null)
  const benchmark = ref([])
  const trustGaps = ref(null)
  const killerMetricsTrend = ref(null)
  const scarHotspots = ref(null)

  const loading = ref(false)
  const error = ref(null)

  // Computed
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)

  // Actions
  async function fetchExecutiveSummary() {
    loading.value = true
    error.value = null
    try {
      const response = await dashboardService.getExecutiveSummary()
      executive.value = response.data || response
      return executive.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch executive summary'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchBenchmarkData() {
    loading.value = true
    error.value = null
    try {
      const response = await dashboardService.getBenchmarkData()
      benchmark.value = response.data || response
      return benchmark.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch benchmark data'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTrustGapsData() {
    loading.value = true
    error.value = null
    try {
      const response = await dashboardService.getTrustGapsData()
      trustGaps.value = response.data || response
      return trustGaps.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch trust gaps data'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchKillerMetricsTrendData() {
    loading.value = true
    error.value = null
    try {
      const response = await dashboardService.getKillerMetricsTrendData()
      killerMetricsTrend.value = response.data || response
      return killerMetricsTrend.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch killer metrics trend data'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchScarHotspotsData() {
    loading.value = true
    error.value = null
    try {
      const response = await dashboardService.getScarHotspotsData()
      scarHotspots.value = response.data || response
      return scarHotspots.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch scar hotspots data'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // Fetch all dashboard data
  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      const [summaryRes, benchmarkRes] = await Promise.all([
        dashboardService.getExecutiveSummary(),
        dashboardService.getBenchmarkData()
      ])

      executive.value = summaryRes.data || summaryRes
      benchmark.value = benchmarkRes.data || benchmarkRes

      return {
        executive: executive.value,
        benchmark: benchmark.value
      }
    } catch (err) {
      error.value = err.message || 'Failed to fetch dashboard data'
      console.error('Dashboard store error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // Clear state
  function clearDashboard() {
    executive.value = null
    benchmark.value = []
    trustGaps.value = null
    killerMetricsTrend.value = null
    scarHotspots.value = null
    error.value = null
  }

  return {
    // State
    executive,
    benchmark,
    trustGaps,
    killerMetricsTrend,
    scarHotspots,
    loading,
    error,

    // Computed
    isLoading,
    hasError,

    // Actions
    fetchExecutiveSummary,
    fetchBenchmarkData,
    fetchTrustGapsData,
    fetchKillerMetricsTrendData,
    fetchScarHotspotsData,
    fetchDashboard,
    clearDashboard
  }
})
