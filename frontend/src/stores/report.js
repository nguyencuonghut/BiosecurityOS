import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as reportService from '@/services/reportService.js'
import apiClient from '@/api/client.js'

export const useReportStore = defineStore('report', () => {
  const reports = ref([])
  const loading = ref(false)
  const generating = ref(false)

  async function fetchReports() {
    loading.value = true
    try {
      const res = await reportService.listReports({ page_size: 100, sort: '-created_at' })
      reports.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function generateReport(payload) {
    generating.value = true
    try {
      const report = await reportService.createReport(payload)
      reports.value.unshift(report)
      return report
    } finally {
      generating.value = false
    }
  }

  async function downloadReport(reportId) {
    const response = await reportService.downloadReport(reportId)
    const disposition = response.headers['content-disposition'] || ''
    const match = disposition.match(/filename="?(.+?)"?$/i)
    const filename = match ? match[1] : `report-${reportId}`

    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  async function viewReportPdf(reportId) {
    const response = await apiClient.get(`/reports/${reportId}/download`, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  return { reports, loading, generating, fetchReports, generateReport, downloadReport, viewReportPdf }
})
