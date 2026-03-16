import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as scorecardService from '@/services/scorecardService.js'

export const useScorecardStore = defineStore('scorecard', () => {
  // ── List state ──
  const templates = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({ page: 1, page_size: 20, farm_type: null, status: null })

  // ── Detail state ──
  const currentTemplate = ref(null)
  const sections = ref([])

  // ── Actions ──
  async function fetchTemplates() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.farm_type) params.farm_type = filters.value.farm_type
      if (filters.value.ownership_type) params.ownership_type = filters.value.ownership_type
      if (filters.value.status) params.status = filters.value.status

      const result = await scorecardService.listTemplates(params)
      templates.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  async function fetchTemplate(id) {
    loading.value = true
    try {
      currentTemplate.value = await scorecardService.getTemplate(id)
      sections.value = currentTemplate.value.sections || []
    } finally {
      loading.value = false
    }
  }

  async function saveTemplate(payload, id = null) {
    if (id) {
      currentTemplate.value = await scorecardService.updateTemplate(id, payload)
    } else {
      currentTemplate.value = await scorecardService.createTemplate(payload)
    }
    return currentTemplate.value
  }

  async function activateTemplate(id) {
    const result = await scorecardService.activateTemplate(id)
    if (currentTemplate.value?.id === id) currentTemplate.value = result
    return result
  }

  async function archiveTemplate(id) {
    const result = await scorecardService.archiveTemplate(id)
    if (currentTemplate.value?.id === id) currentTemplate.value = result
    return result
  }

  // ── Section ──
  async function fetchSections(templateId) {
    sections.value = await scorecardService.listSections(templateId)
  }

  async function saveSection(templateId, payload, sectionId = null) {
    if (sectionId) {
      const updated = await scorecardService.updateSection(sectionId, payload)
      const idx = sections.value.findIndex((s) => s.id === sectionId)
      if (idx !== -1) sections.value[idx] = { ...sections.value[idx], ...updated }
      return updated
    }
    const created = await scorecardService.createSection(templateId, payload)
    sections.value.push({ ...created, items: [] })
    return created
  }

  // ── Item ──
  async function saveItem(sectionId, payload, itemId = null) {
    if (itemId) {
      const updated = await scorecardService.updateItem(itemId, payload)
      const section = sections.value.find((s) => s.id === sectionId)
      if (section?.items) {
        const idx = section.items.findIndex((i) => i.id === itemId)
        if (idx !== -1) section.items[idx] = updated
      }
      return updated
    }
    const created = await scorecardService.createItem(sectionId, payload)
    const section = sections.value.find((s) => s.id === sectionId)
    if (section) {
      if (!section.items) section.items = []
      section.items.push(created)
    }
    return created
  }

  async function removeItem(sectionId, itemId) {
    await scorecardService.deleteItem(itemId)
    const section = sections.value.find((s) => s.id === sectionId)
    if (section?.items) {
      section.items = section.items.filter((i) => i.id !== itemId)
    }
  }

  return {
    templates, totalRecords, loading, filters,
    currentTemplate, sections,
    fetchTemplates, fetchTemplate, saveTemplate,
    activateTemplate, archiveTemplate,
    fetchSections, saveSection,
    saveItem, removeItem,
  }
})
