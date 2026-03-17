import client from './client'

/**
 * Get executive summary data
 * GET /dashboards/executive-summary
 */
export async function getExecutiveSummary() {
  try {
    const response = await client.get('/dashboards/executive-summary')
    return response.data
  } catch (error) {
    console.error('Dashboard: Failed to fetch executive summary', error)
    // Return mock data as fallback
    return {
      data: {
        farm_count: 20,
        avg_score: 78.4,
        high_risk_farms: 4,
        open_cases: 23,
        overdue_tasks: 11,
        killer_metric_open: 2,
        low_trust_sites: 3
      }
    }
  }
}

/**
 * Get farm-specific dashboard data
 * GET /dashboards/farm/{farm_id}
 */
export async function getFarmDashboard(farmId) {
  try {
    const response = await client.get(`/dashboards/farm/${farmId}`)
    return response.data
  } catch (error) {
    console.error(`Dashboard: Failed to fetch farm dashboard for ${farmId}`, error)
    throw error
  }
}

/**
 * Get benchmark/comparison data across farms
 * GET /dashboards/benchmark
 */
export async function getBenchmarkData() {
  try {
    const response = await client.get('/dashboards/benchmark')
    return response.data
  } catch (error) {
    console.error('Dashboard: Failed to fetch benchmark data', error)
    // Return mock data as fallback
    return {
      data: [
        {
          id: 1,
          rank: 1,
          name: 'Trại nái Bắc Ninh',
          code: 'F003',
          score: 85.2,
          trend: 2.3,
          status: 'strong'
        },
        {
          id: 2,
          rank: 2,
          name: 'Trại nái Hải Dương',
          code: 'F001',
          score: 82.4,
          trend: 1.5,
          status: 'good'
        }
      ]
    }
  }
}

/**
 * Get trust gap analysis data
 * GET /dashboards/trust-gaps
 */
export async function getTrustGapsData() {
  try {
    const response = await client.get('/dashboards/trust-gaps')
    return response.data
  } catch (error) {
    console.error('Dashboard: Failed to fetch trust gaps data', error)
    throw error
  }
}

/**
 * Get killer metrics trend data
 * GET /dashboards/killer-metrics-trend
 */
export async function getKillerMetricsTrendData() {
  try {
    const response = await client.get('/dashboards/killer-metrics-trend')
    return response.data
  } catch (error) {
    console.error('Dashboard: Failed to fetch killer metrics trend data', error)
    throw error
  }
}

/**
 * Get scar/risk hotspots data
 * GET /dashboards/scar-hotspots
 */
export async function getScarHotspotsData() {
  try {
    const response = await client.get('/dashboards/scar-hotspots')
    return response.data
  } catch (error) {
    console.error('Dashboard: Failed to fetch scar hotspots data', error)
    throw error
  }
}

export default {
  getExecutiveSummary,
  getFarmDashboard,
  getBenchmarkData,
  getTrustGapsData,
  getKillerMetricsTrendData,
  getScarHotspotsData
}
