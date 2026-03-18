import apiClient from '@/api/client.js'

// ── Task CRUD ──────────────────────────────────────────────────

export async function listTasks(params = {}) {
  const { data } = await apiClient.get('/tasks', { params })
  return data // { data: [...], meta }
}

export async function getTask(id) {
  const { data } = await apiClient.get(`/tasks/${id}`)
  return data.data
}

export async function createTask(payload) {
  const { data } = await apiClient.post('/tasks', payload)
  return data.data
}

export async function updateTask(id, payload) {
  const { data } = await apiClient.patch(`/tasks/${id}`, payload)
  return data.data
}

// ── Status Management ──────────────────────────────────────────

export async function changeStatus(taskId, targetStatus, version) {
  const { data } = await apiClient.post(`/tasks/${taskId}/change-status`, { target_status: targetStatus, version })
  return data.data
}

export async function submitForReview(taskId, version) {
  const { data } = await apiClient.post(`/tasks/${taskId}/submit-for-review`, { version })
  return data.data
}

export async function closeTask(taskId, version) {
  const { data } = await apiClient.post(`/tasks/${taskId}/close`, { version })
  return data.data
}

// ── Assignees ──────────────────────────────────────────────────

export async function addAssignee(taskId, payload) {
  const { data } = await apiClient.post(`/tasks/${taskId}/assignees`, payload)
  return data.data
}

export async function removeAssignee(taskId, assigneeId) {
  await apiClient.delete(`/tasks/${taskId}/assignees/${assigneeId}`)
}

// ── Evidence/Attachments ───────────────────────────────────────

export async function addTaskAttachment(taskId, payload) {
  const { data } = await apiClient.post(`/tasks/${taskId}/attachments`, payload)
  return data.data
}

// ── Reviews ────────────────────────────────────────────────────

export async function listReviews(taskId) {
  const { data } = await apiClient.get(`/tasks/${taskId}/reviews`)
  return data.data
}

export async function approveTask(taskId, reviewNote) {
  const { data } = await apiClient.post(`/tasks/${taskId}/approve`, { review_note: reviewNote })
  return data.data
}

export async function rejectTask(taskId, reviewNote, nextActionDueAt) {
  const { data } = await apiClient.post(`/tasks/${taskId}/reject`, { review_note: reviewNote, next_action_due_at: nextActionDueAt })
  return data.data
}

// ── Comments ───────────────────────────────────────────────────

export async function addComment(taskId, commentText, commentType = 'note') {
  const { data } = await apiClient.post(`/tasks/${taskId}/comments`, { comment_text: commentText, comment_type: commentType })
  return data.data
}
