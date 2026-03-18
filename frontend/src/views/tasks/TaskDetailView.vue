<script setup>
/**
 * F06.2 — Task Detail + Evidence Review (wireframe §4.8)
 * Layout: Header → Status pipeline → Tabs (Overview | Evidence | Reviews | Comments)
 * Actions: Status transitions, Submit for review, Approve, Reject, Close
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Breadcrumb from 'primevue/breadcrumb'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import Step from 'primevue/step'
import Divider from 'primevue/divider'
import DatePicker from 'primevue/datepicker'
import FileUploader from '@/components/tasks/FileUploader.vue'
import EvidenceGallery from '@/components/tasks/EvidenceGallery.vue'
import { useTaskStore } from '@/stores/task.js'
import { useAuthStore } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const store = useTaskStore()
const authStore = useAuthStore()

const activeTab = ref('0')
const task = computed(() => store.currentTask)

// ── Breadcrumb ──
const breadcrumbItems = computed(() => [
  { label: 'Tasks', command: () => router.push('/tasks') },
  { label: task.value?.task_no || '...' },
])
const breadcrumbHome = { icon: 'pi pi-check-square', command: () => router.push('/tasks') }

// ── Status pipeline ──
const STATUS_PIPELINE = ['open', 'accepted', 'in_progress', 'pending_review', 'closed']
const statusStepIndex = computed(() => {
  if (!task.value) return -1
  if (task.value.status === 'cancelled') return -1
  if (task.value.status === 'needs_rework') return 2 // back to in_progress position
  return STATUS_PIPELINE.indexOf(task.value.status)
})

const VALID_TRANSITIONS = {
  open: ['accepted', 'cancelled'],
  accepted: ['in_progress', 'cancelled'],
  in_progress: ['cancelled'],
  needs_rework: ['cancelled'],
}

function nextActions(status) {
  return VALID_TRANSITIONS[status] || []
}

// ── Status change ──
const showStatusDialog = ref(false)
const targetStatus = ref(null)

function openStatusDialog(target) {
  targetStatus.value = target
  showStatusDialog.value = true
}

async function confirmStatusChange() {
  try {
    await store.changeStatus(task.value.id, targetStatus.value, task.value.version)
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã chuyển sang ${statusLabel(targetStatus.value)}`, life: 3000 })
    showStatusDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Submit for review ──
async function handleSubmitForReview() {
  try {
    await store.submitForReview(task.value.id, task.value.version)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã gửi yêu cầu review', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Close task ──
async function handleCloseTask() {
  try {
    await store.closeTask(task.value.id, task.value.version)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Task đã đóng', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Review (Approve / Reject) ──
const showReviewDialog = ref(false)
const reviewAction = ref('approve')
const reviewNote = ref('')
const nextActionDueAt = ref(null)

function openReviewDialog(action) {
  reviewAction.value = action
  reviewNote.value = ''
  nextActionDueAt.value = null
  showReviewDialog.value = true
}

async function submitReview() {
  try {
    if (reviewAction.value === 'approve') {
      await store.approveTask(task.value.id, reviewNote.value || null)
      toast.add({ severity: 'success', summary: 'Đã phê duyệt', detail: 'Task đã được approve', life: 3000 })
    } else {
      await store.rejectTask(
        task.value.id,
        reviewNote.value || null,
        nextActionDueAt.value ? new Date(nextActionDueAt.value).toISOString() : null,
      )
      toast.add({ severity: 'warn', summary: 'Đã từ chối', detail: 'Task cần rework', life: 3000 })
    }
    showReviewDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Assignee management ──
const showAssigneeDialog = ref(false)
const assigneeForm = ref({ user_id: '', responsibility_type: 'support' })
const userOptions = ref([])

const responsibilityOptions = [
  { label: 'Owner', value: 'owner' },
  { label: 'Support', value: 'support' },
]

async function openAssigneeDialog() {
  try {
    const { listUsers } = await import('@/services/userService.js')
    const result = await listUsers({ page_size: 100 })
    userOptions.value = result.data.filter(u => u.status === 'active')
  } catch {
    userOptions.value = []
  }
  assigneeForm.value = { user_id: '', responsibility_type: 'support' }
  showAssigneeDialog.value = true
}

async function submitAssignee() {
  try {
    await store.addAssignee(task.value.id, assigneeForm.value)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm assignee', life: 3000 })
    showAssigneeDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

async function handleRemoveAssignee(assignee) {
  try {
    await store.removeAssignee(task.value.id, assignee.id)
    toast.add({ severity: 'success', summary: 'Đã xóa', detail: 'Đã xóa assignee', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Comments ──
const commentText = ref('')

async function submitComment() {
  if (!commentText.value.trim()) return
  try {
    await store.addComment(task.value.id, commentText.value.trim())
    toast.add({ severity: 'success', summary: 'Đã gửi', detail: 'Comment đã được thêm', life: 3000 })
    commentText.value = ''
    // Reload comments via task detail
    await store.fetchTask(task.value.id)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Evidence upload callback ──
async function onEvidenceUploaded() {
  toast.add({ severity: 'success', summary: 'Upload thành công', detail: 'Evidence đã được tải lên', life: 3000 })
  await store.fetchTask(task.value.id)
}

async function onEvidenceDeleted() {
  toast.add({ severity: 'success', summary: 'Xóa thành công', detail: 'File bằng chứng đã được xóa', life: 3000 })
  await store.fetchTask(task.value.id)
}

// ── Helpers ──
function priorityColor(p) {
  const m = { P0: 'danger', P1: 'warn', P2: 'info', P3: 'secondary' }
  return m[p] || 'secondary'
}
function statusColor(s) {
  const m = { open: 'info', accepted: 'info', in_progress: 'warn', pending_review: 'warn', needs_rework: 'danger', closed: 'success', cancelled: 'secondary' }
  return m[s] || 'secondary'
}
function statusLabel(s) {
  const m = { open: 'Mở', accepted: 'Chấp nhận', in_progress: 'Đang thực hiện', pending_review: 'Đang review', needs_rework: 'Cần rework', closed: 'Đã đóng', cancelled: 'Đã hủy' }
  return m[s] || s
}
function taskTypeLabel(t) {
  const m = { corrective: 'Corrective', preventive: 'Preventive', inspection: 'Inspection', training: 'Training', capex: 'CapEx' }
  return m[t] || t
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function reviewResultLabel(r) {
  const m = { approved: 'Đã duyệt', needs_rework: 'Cần rework', rejected: 'Từ chối' }
  return m[r] || r
}
function reviewResultColor(r) {
  const m = { approved: 'success', needs_rework: 'danger', rejected: 'danger' }
  return m[r] || 'secondary'
}

// ── Can actions ──
const canSubmitForReview = computed(() =>
  task.value && (task.value.status === 'in_progress' || task.value.status === 'needs_rework'))
const canReview = computed(() =>
  task.value?.status === 'pending_review' && authStore.hasPermission('TASK_REVIEW'))
const canClose = computed(() => {
  if (!task.value || task.value.status === 'closed' || task.value.status === 'cancelled') return false
  return store.reviews.some(r => r.review_result === 'approved')
})

// ── Init ──
onMounted(async () => {
  const id = route.params.id
  await store.fetchTask(id)
  await store.fetchReviews(id)
})
</script>

<template>
  <Toast />
  <div class="task-detail-page" v-if="task">
    <!-- Breadcrumb -->
    <Breadcrumb :model="breadcrumbItems" :home="breadcrumbHome" class="task-breadcrumb" />

    <!-- Task Header -->
    <div class="task-header">
      <div class="header-top">
        <div class="header-title-block">
          <h1 class="task-title">{{ task.task_no }} <span class="title-sep">—</span> {{ task.title }}</h1>
          <div class="header-tags">
            <Tag :value="taskTypeLabel(task.task_type)" severity="secondary" />
            <Tag :value="task.priority" :severity="priorityColor(task.priority)" />
            <Tag :value="statusLabel(task.status)" :severity="statusColor(task.status)" />
          </div>
        </div>
        <div class="header-actions">
          <!-- State transitions -->
          <Button
            v-for="target in nextActions(task.status)"
            :key="target"
            :label="statusLabel(target)"
            size="small"
            :severity="statusColor(target)"
            outlined
            @click="openStatusDialog(target)"
          />
          <!-- Submit for review -->
          <Button
            v-if="canSubmitForReview"
            label="Submit for Review"
            icon="pi pi-send"
            size="small"
            severity="info"
            @click="handleSubmitForReview"
          />
          <!-- Review -->
          <Button
            v-if="canReview"
            label="Approve"
            icon="pi pi-check"
            size="small"
            severity="success"
            @click="openReviewDialog('approve')"
          />
          <Button
            v-if="canReview"
            label="Reject"
            icon="pi pi-times"
            size="small"
            severity="danger"
            outlined
            @click="openReviewDialog('reject')"
          />
          <!-- Close -->
          <Button
            v-if="canClose"
            label="Close Task"
            icon="pi pi-lock"
            size="small"
            severity="success"
            @click="handleCloseTask"
          />
        </div>
      </div>

      <!-- Status Pipeline -->
      <div class="pipeline-wrap" v-if="task.status !== 'cancelled'">
        <Stepper :value="statusStepIndex" linear class="task-stepper">
          <StepList>
            <Step v-for="(step, idx) in STATUS_PIPELINE" :key="step" :value="idx">
              {{ statusLabel(step) }}
            </Step>
          </StepList>
        </Stepper>
      </div>
      <div v-else class="cancelled-banner">
        <i class="pi pi-ban"></i> Task đã bị hủy
      </div>
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab" class="task-tabs">
      <TabList>
        <Tab value="0">Tổng quan</Tab>
        <Tab value="1">Bằng chứng</Tab>
        <Tab value="2">Reviews</Tab>
        <Tab value="3">Bình luận</Tab>
      </TabList>
      <TabPanels>
        <!-- Tab 0: Overview -->
        <TabPanel value="0">
          <div class="overview-grid">
            <div class="overview-left">
              <div class="info-card">
                <h3>Chi tiết Task</h3>
                <div class="info-row">
                  <label>Mô tả</label>
                  <p>{{ task.description }}</p>
                </div>
                <div class="info-row" v-if="task.completion_criteria">
                  <label>Tiêu chí hoàn thành</label>
                  <p>{{ task.completion_criteria }}</p>
                </div>
                <div class="info-row" v-if="task.evidence_requirement">
                  <label>Yêu cầu bằng chứng</label>
                  <p>{{ task.evidence_requirement }}</p>
                </div>
                <Divider />
                <div class="info-meta">
                  <div class="meta-item">
                    <label>Hạn SLA</label>
                    <span>{{ formatDate(task.sla_due_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Hạn hoàn thành</label>
                    <span>{{ formatDate(task.completion_due_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Ngày tạo</label>
                    <span>{{ formatDate(task.created_at) }}</span>
                  </div>
                  <div class="meta-item" v-if="task.closed_at">
                    <label>Ngày đóng</label>
                    <span>{{ formatDate(task.closed_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Version</label>
                    <span>{{ task.version }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="overview-right">
              <!-- Assignees -->
              <div class="info-card">
                <div class="card-header-row">
                  <h3>Assignees</h3>
                  <Button icon="pi pi-plus" size="small" text rounded @click="openAssigneeDialog" />
                </div>
                <div v-if="task.assignees?.length" class="assignee-list">
                  <div v-for="a in task.assignees" :key="a.id" class="assignee-item">
                    <div class="assignee-info">
                      <i class="pi pi-user"></i>
                      <span class="assignee-id">{{ a.user_id.slice(0, 8) }}...</span>
                      <Tag :value="a.responsibility_type" :severity="a.responsibility_type === 'owner' ? 'warn' : 'secondary'" class="ml-2" />
                    </div>
                    <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleRemoveAssignee(a)" />
                  </div>
                </div>
                <p v-else class="muted">Chưa có assignee nào</p>
              </div>

              <!-- Latest Review Summary -->
              <div class="info-card" v-if="store.reviews.length">
                <h3>Review gần nhất</h3>
                <div class="review-summary">
                  <Tag :value="reviewResultLabel(store.reviews[0].review_result)" :severity="reviewResultColor(store.reviews[0].review_result)" />
                  <span class="review-date">{{ formatDate(store.reviews[0].reviewed_at) }}</span>
                </div>
                <p v-if="store.reviews[0].review_note" class="review-note-text">{{ store.reviews[0].review_note }}</p>
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- Tab 1: Evidence -->
        <TabPanel value="1">
          <div class="evidence-section">
            <div class="section-header">
              <h3>Bằng chứng (Evidence)</h3>
            </div>
            <FileUploader
              v-if="task.status !== 'closed' && task.status !== 'cancelled'"
              :task-id="task.id"
              @uploaded="onEvidenceUploaded"
            />
            <EvidenceGallery :task-attachments="task.task_attachments || []" @deleted="onEvidenceDeleted" />
          </div>
        </TabPanel>

        <!-- Tab 2: Reviews -->
        <TabPanel value="2">
          <div class="reviews-section">
            <h3>Lịch sử Review</h3>
            <div v-if="store.reviews.length" class="review-list">
              <div v-for="review in store.reviews" :key="review.id" class="review-card">
                <div class="review-header">
                  <Tag :value="reviewResultLabel(review.review_result)" :severity="reviewResultColor(review.review_result)" />
                  <span class="review-date">{{ formatDate(review.reviewed_at) }}</span>
                </div>
                <p v-if="review.review_note" class="review-note-text">{{ review.review_note }}</p>
                <p class="review-meta">Reviewer: {{ review.reviewer_user_id.slice(0, 8) }}...</p>
                <p v-if="review.next_action_due_at" class="review-meta">Hạn rework: {{ formatDate(review.next_action_due_at) }}</p>
              </div>
            </div>
            <p v-else class="muted">Chưa có review nào.</p>
          </div>
        </TabPanel>

        <!-- Tab 3: Comments -->
        <TabPanel value="3">
          <div class="comments-section">
            <h3>Bình luận</h3>
            <div class="comment-input">
              <Textarea v-model="commentText" rows="3" placeholder="Nhập bình luận..." class="w-full" />
              <Button label="Gửi" icon="pi pi-send" size="small" class="mt-2" @click="submitComment" :disabled="!commentText.trim()" />
            </div>
            <p class="muted mt-3">Bình luận sẽ hiển thị sau khi tải lại trang chi tiết.</p>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>

  <!-- Loading state -->
  <div v-else class="loading-state">
    <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
    <p>Đang tải task...</p>
  </div>

  <!-- Status Change Dialog -->
  <Dialog v-model:visible="showStatusDialog" header="Xác nhận chuyển trạng thái" modal :style="{ width: '420px' }">
    <p>Bạn có chắc muốn chuyển task sang trạng thái <strong>{{ statusLabel(targetStatus) }}</strong>?</p>
    <template #footer>
      <Button label="Hủy" severity="secondary" text @click="showStatusDialog = false" />
      <Button label="Xác nhận" @click="confirmStatusChange" />
    </template>
  </Dialog>

  <!-- Review Dialog -->
  <Dialog v-model:visible="showReviewDialog" :header="reviewAction === 'approve' ? 'Phê duyệt Task' : 'Từ chối Task'" modal :style="{ width: '480px' }">
    <div class="form-grid">
      <div class="form-field">
        <label>Ghi chú review</label>
        <Textarea v-model="reviewNote" rows="3" :placeholder="reviewAction === 'approve' ? 'Ghi chú phê duyệt (tùy chọn)...' : 'Lý do từ chối (bắt buộc)...'" class="w-full" />
      </div>
      <div class="form-field" v-if="reviewAction === 'reject'">
        <label>Hạn rework</label>
        <DatePicker v-model="nextActionDueAt" showTime hourFormat="24" placeholder="Hạn hoàn thành rework" class="w-full" />
      </div>
    </div>
    <template #footer>
      <Button label="Hủy" severity="secondary" text @click="showReviewDialog = false" />
      <Button
        :label="reviewAction === 'approve' ? 'Phê duyệt' : 'Từ chối'"
        :icon="reviewAction === 'approve' ? 'pi pi-check' : 'pi pi-times'"
        :severity="reviewAction === 'approve' ? 'success' : 'danger'"
        @click="submitReview"
      />
    </template>
  </Dialog>

  <!-- Assignee Dialog -->
  <Dialog v-model:visible="showAssigneeDialog" header="Thêm Assignee" modal :style="{ width: '420px' }">
    <div class="form-grid">
      <div class="form-field">
        <label>Người dùng <span class="req">*</span></label>
        <Select
          v-model="assigneeForm.user_id"
          :options="userOptions"
          optionLabel="full_name"
          optionValue="id"
          placeholder="Chọn người dùng"
          class="w-full"
          filter
        />
      </div>
      <div class="form-field">
        <label>Vai trò</label>
        <Select v-model="assigneeForm.responsibility_type" :options="responsibilityOptions" optionLabel="label" optionValue="value" class="w-full" />
      </div>
    </div>
    <template #footer>
      <Button label="Hủy" severity="secondary" text @click="showAssigneeDialog = false" />
      <Button label="Thêm" icon="pi pi-plus" @click="submitAssignee" :disabled="!assigneeForm.user_id" />
    </template>
  </Dialog>
</template>

<style scoped>
.task-detail-page { width: 100%; }

.task-breadcrumb { margin-bottom: 1rem; }

/* Header */
.task-header {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;
}
.header-top { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; }
.header-title-block { flex: 1; min-width: 0; }
.task-title { margin: 0 0 0.5rem; font-size: 1.25rem; }
.title-sep { color: var(--p-text-muted-color); margin: 0 0.25rem; }
.header-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

.pipeline-wrap { margin-top: 1.25rem; }
.cancelled-banner {
  margin-top: 1rem; padding: 0.75rem 1rem;
  background: var(--p-red-50); color: var(--p-red-600);
  border-radius: 6px; font-weight: 600;
}

/* Tabs */
.task-tabs { margin-top: 0; }

/* Overview */
.overview-grid { display: grid; grid-template-columns: 1fr 340px; gap: 1.5rem; }
.info-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem;
}
.info-card h3 { margin: 0 0 1rem; font-size: 1rem; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }
.card-header-row h3 { margin-bottom: 0; }

.info-row { margin-bottom: 1rem; }
.info-row label { display: block; font-size: 0.75rem; color: var(--p-text-muted-color); font-weight: 600; margin-bottom: 0.25rem; }
.info-row p { margin: 0; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }

.info-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.meta-item label { display: block; font-size: 0.75rem; color: var(--p-text-muted-color); font-weight: 600; margin-bottom: 0.15rem; }
.meta-item span { font-size: 0.85rem; }

/* Assignees */
.assignee-list { display: flex; flex-direction: column; gap: 0.5rem; }
.assignee-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-radius: 6px; background: var(--p-surface-ground); }
.assignee-info { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.ml-2 { margin-left: 0.5rem; }

/* Reviews */
.review-list { display: flex; flex-direction: column; gap: 0.75rem; }
.review-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1rem;
}
.review-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
.review-date { font-size: 0.8rem; color: var(--p-text-muted-color); }
.review-note-text { margin: 0.5rem 0; font-size: 0.9rem; line-height: 1.4; }
.review-meta { margin: 0.25rem 0 0; font-size: 0.8rem; color: var(--p-text-muted-color); }
.review-summary { display: flex; align-items: center; gap: 0.75rem; }

/* Evidence */
.evidence-section { }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-header h3 { margin: 0; }

/* Comments */
.comments-section { max-width: 700px; }
.comment-input { margin-bottom: 1rem; }

/* Utility */
.muted { color: var(--p-text-muted-color); font-size: 0.85rem; }
.loading-state { text-align: center; padding: 3rem; color: var(--p-text-muted-color); }
.form-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.form-field { display: flex; flex-direction: column; gap: 0.35rem; }
.form-field label { font-weight: 600; font-size: 0.85rem; }
.req { color: var(--p-red-500); }
.w-full { width: 100%; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }

@media (max-width: 768px) {
  .overview-grid { grid-template-columns: 1fr; }
  .header-top { flex-direction: column; }
}
</style>
