<script setup>
/**
 * F06.1 — Task List View (wireframe §4.8)
 * Danh sách corrective task với bộ lọc, quick preview, và tạo task.
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import { useTaskStore } from '@/stores/task.js'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const toast = useToast()
const store = useTaskStore()
const farmStore = useFarmStore()
const authStore = useAuthStore()

// ── Filter options ──
const priorityOptions = [
  { label: 'Tất cả', value: null },
  { label: 'P0 — Khẩn cấp', value: 'P0' },
  { label: 'P1 — Rất cao', value: 'P1' },
  { label: 'P2 — Trung bình', value: 'P2' },
  { label: 'P3 — Dài hạn', value: 'P3' },
]

const statusOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Mở', value: 'open' },
  { label: 'Đã chấp nhận', value: 'accepted' },
  { label: 'Đang thực hiện', value: 'in_progress' },
  { label: 'Đang review', value: 'pending_review' },
  { label: 'Cần rework', value: 'needs_rework' },
  { label: 'Đã đóng', value: 'closed' },
  { label: 'Đã hủy', value: 'cancelled' },
]

const taskTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Corrective', value: 'corrective' },
  { label: 'Preventive', value: 'preventive' },
  { label: 'Inspection', value: 'inspection' },
  { label: 'Training', value: 'training' },
  { label: 'CapEx', value: 'capex' },
]

const farmOptions = computed(() => [
  { label: 'Tất cả trại', value: null },
  ...farmStore.farms.map(f => ({ label: f.name, value: f.id })),
])

// ── Quick preview ──
const selectedTask = ref(null)

// ── Create dialog ──
const showCreate = ref(false)
const createForm = ref({
  case_id: '', title: '', description: '',
  task_type: 'corrective', priority: 'P2',
  completion_due_at: null, completion_criteria: '', evidence_requirement: '',
})

// ── Helpers ──
function priorityColor(p) {
  const m = { P0: 'danger', P1: 'warn', P2: 'info', P3: 'secondary' }
  return m[p] || 'secondary'
}

function statusColor(s) {
  const m = {
    open: 'info', accepted: 'info', in_progress: 'warn',
    pending_review: 'warn', needs_rework: 'danger',
    closed: 'success', cancelled: 'secondary',
  }
  return m[s] || 'secondary'
}

function statusLabel(s) {
  const m = {
    open: 'Mở', accepted: 'Chấp nhận', in_progress: 'Đang thực hiện',
    pending_review: 'Đang review', needs_rework: 'Cần rework',
    closed: 'Đã đóng', cancelled: 'Đã hủy',
  }
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

function formatShortDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

function isOverdue(task) {
  if (!task.completion_due_at || task.status === 'closed' || task.status === 'cancelled') return false
  return new Date(task.completion_due_at) < new Date()
}

// ── Actions ──
function onFilter() {
  store.filters.page = 1
  store.fetchTasks()
}

function onPage(e) {
  store.filters.page = e.page + 1
  store.filters.page_size = e.rows
  store.fetchTasks()
}

function onRowSelect(event) {
  selectedTask.value = event.data
}

function openDetail(task) {
  router.push({ name: 'TaskDetail', params: { id: task.id } })
}

function openCreate() {
  createForm.value = {
    case_id: '', title: '', description: '',
    task_type: 'corrective', priority: 'P2',
    completion_due_at: null, completion_criteria: '', evidence_requirement: '',
  }
  showCreate.value = true
}

async function submitCreate() {
  try {
    const payload = { ...createForm.value }
    if (payload.completion_due_at) {
      payload.completion_due_at = new Date(payload.completion_due_at).toISOString()
    } else {
      delete payload.completion_due_at
    }
    if (!payload.completion_criteria) delete payload.completion_criteria
    if (!payload.evidence_requirement) delete payload.evidence_requirement
    const created = await store.createTask(payload)
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã tạo ${created.task_no}`, life: 3000 })
    showCreate.value = false
    store.fetchTasks()
  } catch (e) {
    const msg = e.response?.data?.error?.message || 'Có lỗi xảy ra'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 5000 })
  }
}

onMounted(async () => {
  await farmStore.fetchFarms()
  await store.fetchTasks()
})
</script>

<template>
  <Toast />
  <div class="task-list-page">
    <div class="page-header">
      <div>
        <h2><i class="pi pi-check-square" style="color: var(--p-primary-color)"></i> Corrective Tasks</h2>
        <p class="subtitle">Quản lý hành động khắc phục — theo dõi SLA, evidence, review</p>
      </div>
      <Button
        v-if="authStore.hasPermission('TASK_CREATE')"
        label="Tạo Task"
        icon="pi pi-plus"
        @click="openCreate"
      />
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <Select v-model="store.filters.farm_id" :options="farmOptions" optionLabel="label" optionValue="value" placeholder="Trại" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.priority" :options="priorityOptions" optionLabel="label" optionValue="value" placeholder="Mức ưu tiên" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.status" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Trạng thái" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.task_type" :options="taskTypeOptions" optionLabel="label" optionValue="value" placeholder="Loại task" class="filter-select" @change="onFilter" />
    </div>

    <!-- Main layout -->
    <div class="task-layout">
      <div class="task-table-wrap">
        <DataTable
          :value="store.tasks"
          :loading="store.loading"
          :lazy="true"
          :paginator="true"
          :rows="20"
          :totalRecords="store.totalRecords"
          :first="(store.filters.page - 1) * store.filters.page_size"
          @page="onPage"
          selectionMode="single"
          v-model:selection="selectedTask"
          @rowSelect="onRowSelect"
          stripedRows
          class="task-table"
        >
          <Column header="Task No" style="width: 130px">
            <template #body="{ data }">
              <a class="task-link" @click.prevent="openDetail(data)">{{ data.task_no }}</a>
            </template>
          </Column>
          <Column header="Loại" style="width: 100px">
            <template #body="{ data }">
              <Tag :value="taskTypeLabel(data.task_type)" severity="secondary" />
            </template>
          </Column>
          <Column header="Ưu tiên" style="width: 85px">
            <template #body="{ data }">
              <Tag :value="data.priority" :severity="priorityColor(data.priority)" />
            </template>
          </Column>
          <Column header="Tiêu đề" style="min-width: 200px">
            <template #body="{ data }">
              <div class="title-cell">{{ data.title }}</div>
            </template>
          </Column>
          <Column header="Hạn" style="width: 90px">
            <template #body="{ data }">
              <span :class="{ overdue: isOverdue(data) }">
                {{ formatShortDate(data.completion_due_at) }}
              </span>
            </template>
          </Column>
          <Column header="Trạng thái" style="width: 130px">
            <template #body="{ data }">
              <Tag :value="statusLabel(data.status)" :severity="statusColor(data.status)" />
            </template>
          </Column>
          <Column header="Tạo lúc" style="width: 130px">
            <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
          </Column>
          <template #empty>
            <div class="empty-msg">Chưa có task nào.</div>
          </template>
        </DataTable>
      </div>

      <!-- Quick preview -->
      <div class="quick-preview" v-if="selectedTask">
        <h4>{{ selectedTask.task_no }}</h4>
        <div class="preview-field">
          <label>Tiêu đề</label>
          <span>{{ selectedTask.title }}</span>
        </div>
        <div class="preview-field">
          <label>Mô tả</label>
          <span>{{ selectedTask.description || '—' }}</span>
        </div>
        <div class="preview-row">
          <div class="preview-field">
            <label>Ưu tiên</label>
            <Tag :value="selectedTask.priority" :severity="priorityColor(selectedTask.priority)" />
          </div>
          <div class="preview-field">
            <label>Loại</label>
            <Tag :value="taskTypeLabel(selectedTask.task_type)" severity="secondary" />
          </div>
        </div>
        <div class="preview-field">
          <label>Trạng thái</label>
          <Tag :value="statusLabel(selectedTask.status)" :severity="statusColor(selectedTask.status)" />
        </div>
        <div class="preview-field">
          <label>Hạn hoàn thành</label>
          <span :class="{ overdue: isOverdue(selectedTask) }">{{ formatDate(selectedTask.completion_due_at) }}</span>
        </div>
        <div class="preview-field" v-if="selectedTask.completion_criteria">
          <label>Tiêu chí hoàn thành</label>
          <span>{{ selectedTask.completion_criteria }}</span>
        </div>
        <Button label="Mở chi tiết" icon="pi pi-arrow-right" class="mt-3 w-full" @click="openDetail(selectedTask)" />
      </div>
    </div>

    <!-- Create Task Dialog -->
    <Dialog v-model:visible="showCreate" header="Tạo Task khắc phục mới" modal :style="{ width: '600px' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Case ID <span class="req">*</span></label>
          <InputText v-model="createForm.case_id" placeholder="UUID của case liên quan" class="w-full" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Loại task</label>
            <Select v-model="createForm.task_type" :options="taskTypeOptions.filter(o => o.value)" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="form-field">
            <label>Mức ưu tiên</label>
            <Select v-model="createForm.priority" :options="priorityOptions.filter(o => o.value)" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="form-field">
          <label>Tiêu đề <span class="req">*</span></label>
          <InputText v-model="createForm.title" placeholder="Mô tả ngắn gọn task" class="w-full" />
        </div>
        <div class="form-field">
          <label>Mô tả <span class="req">*</span></label>
          <Textarea v-model="createForm.description" rows="3" placeholder="Chi tiết hành động cần thực hiện..." class="w-full" />
        </div>
        <div class="form-field">
          <label>Hạn hoàn thành</label>
          <DatePicker v-model="createForm.completion_due_at" showTime hourFormat="24" placeholder="Chọn ngày" class="w-full" />
        </div>
        <div class="form-field">
          <label>Tiêu chí hoàn thành</label>
          <Textarea v-model="createForm.completion_criteria" rows="2" placeholder="Mô tả tiêu chí đánh giá task hoàn thành..." class="w-full" />
        </div>
        <div class="form-field">
          <label>Yêu cầu bằng chứng</label>
          <Textarea v-model="createForm.evidence_requirement" rows="2" placeholder="Loại bằng chứng cần nộp (ảnh, video, tài liệu)..." class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showCreate = false" />
        <Button
          label="Tạo Task"
          icon="pi pi-plus"
          @click="submitCreate"
          :disabled="!createForm.case_id || !createForm.title || !createForm.description"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.task-list-page { width: 100%; }

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;
}
.page-header h2 {
  margin: 0 0 0.25rem; display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;
}
.subtitle { font-size: 0.85rem; color: var(--p-text-muted-color); margin: 0; }

.filter-bar { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.filter-select { min-width: 160px; }

.task-layout { display: flex; gap: 1rem; align-items: flex-start; }
.task-table-wrap { flex: 1; min-width: 0; }

.quick-preview {
  width: 280px; flex-shrink: 0;
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1.25rem;
}
.quick-preview h4 { margin: 0 0 1rem; font-size: 1rem; }

.preview-field { margin-bottom: 0.75rem; }
.preview-field label { display: block; font-size: 0.75rem; color: var(--p-text-muted-color); font-weight: 600; margin-bottom: 0.2rem; }
.preview-field span { font-size: 0.85rem; }
.preview-row { display: flex; gap: 1rem; }

.task-link { color: var(--p-primary-color); cursor: pointer; font-weight: 600; text-decoration: underline; }
.task-link:hover { text-decoration: none; }

.title-cell { font-size: 0.85rem; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.overdue { color: var(--p-red-500); font-weight: 600; }

.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }

.form-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-field { display: flex; flex-direction: column; gap: 0.35rem; }
.form-field label { font-weight: 600; font-size: 0.85rem; }
.req { color: var(--p-red-500); }
.w-full { width: 100%; }
.mt-3 { margin-top: 0.75rem; }
</style>
