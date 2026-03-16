import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as svc from '@/services/killerMetricService.js'

export const useKillerMetricStore = defineStore('killerMetric', () => {
  // ── Definitions ──
  const definitions = ref([])
  const definitionsLoading = ref(false)

  async function fetchDefinitions() {
    definitionsLoading.value = true
    try {
      const result = await svc.listDefinitions()
      definitions.value = result.data
    } finally {
      definitionsLoading.value = false
    }
  }

  async function createDefinition(payload) {
    const created = await svc.createDefinition(payload)
    await fetchDefinitions()
    return created
  }

  async function updateDefinition(id, payload) {
    const updated = await svc.updateDefinition(id, payload)
    await fetchDefinitions()
    return updated
  }

  // ── Events ──
  const events = ref([])
  const totalRecords = ref(0)
  const eventsLoading = ref(false)
  const filters = ref({
    page: 1, page_size: 20,
    farm_id: null, status: null, definition_id: null,
  })
  const currentEvent = ref(null)

  async function fetchEvents() {
    eventsLoading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.farm_id) params.farm_id = filters.value.farm_id
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.definition_id) params.definition_id = filters.value.definition_id

      const result = await svc.listEvents(params)
      events.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      eventsLoading.value = false
    }
  }

  async function fetchEvent(id) {
    eventsLoading.value = true
    try {
      currentEvent.value = await svc.getEvent(id)
    } finally {
      eventsLoading.value = false
    }
  }

  async function createEvent(payload) {
    const created = await svc.createEvent(payload)
    return created
  }

  async function updateEvent(id, payload) {
    const updated = await svc.updateEvent(id, payload)
    if (currentEvent.value?.id === id) currentEvent.value = updated
    return updated
  }

  return {
    definitions, definitionsLoading,
    fetchDefinitions, createDefinition, updateDefinition,
    events, totalRecords, eventsLoading, filters, currentEvent,
    fetchEvents, fetchEvent, createEvent, updateEvent,
  }
})
