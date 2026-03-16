import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as farmService from '@/services/farmService.js'
import * as regionService from '@/services/regionService.js'

export const useFarmStore = defineStore('farm', () => {
  // ── List state ──
  const farms = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({ page: 1, page_size: 20, region_id: null, farm_type: null, ownership_type: null, search: null })

  // ── Detail state ──
  const currentFarm = ref(null)
  const areas = ref([])
  const routes = ref([])
  const riskPoints = ref([])

  // ── Reference data ──
  const regions = ref([])

  // ── Actions ──
  async function fetchFarms() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.region_id) params.region_id = filters.value.region_id
      if (filters.value.farm_type) params.farm_type = filters.value.farm_type
      if (filters.value.ownership_type) params.ownership_type = filters.value.ownership_type
      if (filters.value.sort) params.sort = filters.value.sort
      if (filters.value.search) params.search = filters.value.search

      const result = await farmService.listFarms(params)
      farms.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  async function fetchFarm(id) {
    loading.value = true
    try {
      currentFarm.value = await farmService.getFarm(id)
    } finally {
      loading.value = false
    }
  }

  async function saveFarm(payload, id = null) {
    if (id) {
      currentFarm.value = await farmService.updateFarm(id, payload)
    } else {
      currentFarm.value = await farmService.createFarm(payload)
    }
    return currentFarm.value
  }

  async function fetchAreas(farmId) {
    areas.value = await farmService.listAreas(farmId)
  }

  async function saveArea(farmId, payload, areaId = null) {
    if (areaId) {
      const updated = await farmService.updateArea(farmId, areaId, payload)
      const idx = areas.value.findIndex((a) => a.id === areaId)
      if (idx !== -1) areas.value[idx] = updated
      return updated
    }
    const created = await farmService.createArea(farmId, payload)
    areas.value.push(created)
    return created
  }

  async function fetchRoutes(farmId) {
    routes.value = await farmService.listRoutes(farmId)
  }

  async function saveRoute(farmId, payload) {
    const created = await farmService.createRoute(farmId, payload)
    routes.value.push(created)
    return created
  }

  async function fetchRiskPoints(farmId) {
    riskPoints.value = await farmService.listRiskPoints(farmId)
  }

  async function saveRiskPoint(farmId, payload) {
    const created = await farmService.createRiskPoint(farmId, payload)
    riskPoints.value.push(created)
    return created
  }

  async function fetchRegions() {
    if (regions.value.length) return
    const result = await regionService.listRegions({ page_size: 100 })
    regions.value = result.data
  }

  return {
    farms, totalRecords, loading, filters,
    currentFarm, areas, routes, riskPoints, regions,
    fetchFarms, fetchFarm, saveFarm,
    fetchAreas, saveArea,
    fetchRoutes, saveRoute,
    fetchRiskPoints, saveRiskPoint,
    fetchRegions,
  }
})
