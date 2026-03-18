import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as svc from '@/services/taskService.js'
import * as attachSvc from '@/services/attachmentService.js'

export const useTaskStore = defineStore('task', () => {
  // ── List state ──
  const tasks = ref([])
  const totalRecords = ref(0)
  const loading = ref(false)
  const filters = ref({
    page: 1, page_size: 20,
    farm_id: null, case_id: null, priority: null, status: null,
    assignee_user_id: null, overdue: false,
  })

  async function fetchTasks() {
    loading.value = true
    try {
      const params = { page: filters.value.page, page_size: filters.value.page_size }
      if (filters.value.farm_id) params.farm_id = filters.value.farm_id
      if (filters.value.case_id) params.case_id = filters.value.case_id
      if (filters.value.priority) params.priority = filters.value.priority
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.assignee_user_id) params.assignee_user_id = filters.value.assignee_user_id
      if (filters.value.overdue) params.overdue = filters.value.overdue

      const result = await svc.listTasks(params)
      tasks.value = result.data
      totalRecords.value = result.meta.total
    } finally {
      loading.value = false
    }
  }

  // ── Detail state ──
  const currentTask = ref(null)
  const reviews = ref([])

  async function fetchTask(id) {
    loading.value = true
    try {
      currentTask.value = await svc.getTask(id)
    } finally {
      loading.value = false
    }
  }

  async function fetchReviews(taskId) {
    reviews.value = await svc.listReviews(taskId)
  }

  // ── CRUD ──
  async function createTask(payload) {
    return await svc.createTask(payload)
  }

  async function updateTask(id, payload) {
    const updated = await svc.updateTask(id, payload)
    if (currentTask.value?.id === id) currentTask.value = updated
    return updated
  }

  // ── Status ──
  async function changeStatus(taskId, targetStatus, version) {
    const updated = await svc.changeStatus(taskId, targetStatus, version)
    if (currentTask.value?.id === taskId) currentTask.value = updated
    return updated
  }

  async function submitForReview(taskId, version) {
    const updated = await svc.submitForReview(taskId, version)
    if (currentTask.value?.id === taskId) currentTask.value = updated
    return updated
  }

  async function closeTask(taskId, version) {
    const updated = await svc.closeTask(taskId, version)
    if (currentTask.value?.id === taskId) currentTask.value = updated
    return updated
  }

  // ── Assignees ──
  async function addAssignee(taskId, payload) {
    const assignee = await svc.addAssignee(taskId, payload)
    await fetchTask(taskId)
    return assignee
  }

  async function removeAssignee(taskId, assigneeId) {
    await svc.removeAssignee(taskId, assigneeId)
    await fetchTask(taskId)
  }

  // ── Reviews ──
  async function approveTask(taskId, reviewNote) {
    const review = await svc.approveTask(taskId, reviewNote)
    await Promise.all([fetchReviews(taskId), fetchTask(taskId)])
    return review
  }

  async function rejectTask(taskId, reviewNote, nextActionDueAt) {
    const review = await svc.rejectTask(taskId, reviewNote, nextActionDueAt)
    await Promise.all([fetchReviews(taskId), fetchTask(taskId)])
    return review
  }

  // ── Attachments ──
  async function addTaskAttachment(taskId, payload) {
    return await svc.addTaskAttachment(taskId, payload)
  }

  async function uploadEvidence(taskId, file, uploadStage, onProgress) {
    // Upload file to MinIO
    const attachment = await attachSvc.uploadFile(file, 'task', taskId, onProgress)
    // Link to task
    await svc.addTaskAttachment(taskId, {
      attachment_id: attachment.id,
      upload_stage: uploadStage,
    })
    return attachment
  }

  // ── Comments ──
  async function addComment(taskId, text, type) {
    return await svc.addComment(taskId, text, type)
  }

  return {
    tasks, totalRecords, loading, filters,
    currentTask, reviews,
    fetchTasks, fetchTask, fetchReviews,
    createTask, updateTask,
    changeStatus, submitForReview, closeTask,
    addAssignee, removeAssignee,
    approveTask, rejectTask,
    addTaskAttachment, uploadEvidence,
    addComment,
  }
})
