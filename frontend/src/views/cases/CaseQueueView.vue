<script setup>
/**
 * F05.1 — Case Review Queue (wireframe §4.6)
 * Danh sách case rủi ro với bộ lọc, quick preview, và tạo case.
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
import { useRiskCaseStore } from '@/stores/riskCase.js'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const toast = useToast()
const store = useRiskCaseStore()
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
  { label: 'Mới mở', value: 'open' },
  { label: 'Phân loại', value: 'triage' },
  { label: 'Đang RCA', value: 'in_analysis' },
  { label: 'Đang thực thi', value: 'actioning' },
  { label: 'Theo dõi', value: 'monitoring' },
  { label: 'Đã đóng', value: 'closed' },
  { label: 'Đã hủy', value: 'cancelled' },
]

const caseTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Điểm thấp', value: 'low_score' },
  { label: 'Killer Event', value: 'killer_event' },
  { label: 'Scar', value: 'scar' },
  { label: 'Thủ công', value: 'manual' },
]

const farmOptions = computed(() => [
  { label: 'Tất cả trại', value: null },
  ...farmStore.farms.map(f => ({ label: f.name, value: f.id })),
])

// ── Quick preview ──
const selectedCase = ref(null)

// ── Create case dialog ──
const showCreate = ref(false)
const createForm = ref({
  farm_id: null, case_type: 'manual', title: '', summary: '',
  priority: 'P2', severity: 'medium',
})

const severityCreateOptions = [
  { label: 'Thấp', value: 'low' },
  { label: 'Trung bình', value: 'medium' },
  { label: 'Cao', value: 'high' },
  { label: 'Nghiêm trọng', value: 'critical' },
]

// ── View mode: queue (expert review) or all cases ──
const viewMode = ref('queue')

// ── Helpers ──
function priorityColor(p) {
  const m = { P0: 'danger', P1: 'warn', P2: 'info', P3: 'secondary' }
  return m[p] || 'secondary'
}

function severityColor(s) {
  const m = { critical: 'danger', high: 'warn', medium: 'info', low: 'success' }
  return m[s] || 'secondary'
}

function statusColor(s) {
  const m = {
    open: 'danger', triage: 'warn', in_analysis: 'info',
    actioning: 'warn', monitoring: 'info', closed: 'success', cancelled: 'secondary',
  }
  return m[s] || 'secondary'
}

function statusLabel(s) {
  const m = {
    open: 'Mới mở', triage: 'Phân loại', in_analysis: 'Đang RCA',
    actioning: 'Thực thi', monitoring: 'Theo dõi', closed: 'Đã đóng', cancelled: 'Đã hủy',
  }
  return m[s] || s
}

function caseTypeLabel(t) {
  const m = { low_score: 'Điểm thấp', killer_event: 'Killer Event', scar: 'Scar', manual: 'Thủ công' }
  return m[t] || t
}

function farmName(farmId) {
  return farmStore.farms.find(f => f.id === farmId)?.name || farmId?.slice(0, 8) || '—'
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatShortDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

// ── Actions ──
function onFilter() {
  store.filters.page = 1
  loadData()
}

function onPage(e) {
  if (viewMode.value === 'queue') {
    store.queuePage = e.page + 1
    store.fetchQueue()
  } else {
    store.filters.page = e.page + 1
    store.filters.page_size = e.rows
    store.fetchCases()
  }
}

function loadData() {
  if (viewMode.value === 'queue') {
    store.queuePage = 1
    store.fetchQueue()
  } else {
    store.fetchCases()
  }
}

function switchView(mode) {
  viewMode.value = mode
  loadData()
}

const tableData = computed(() => viewMode.value === 'queue' ? store.queueCases : store.cases)
const tableTotal = computed(() => viewMode.value === 'queue' ? store.queueTotal : store.totalRecords)
const tableLoading = computed(() => viewMode.value === 'queue' ? store.queueLoading : store.loading)

function onRowSelect(event) {
  selectedCase.value = event.data
}

function openDetail(caseItem) {
  router.push({ name: 'CaseDetail', params: { id: caseItem.id } })
}

function openCreate() {
  createForm.value = {
    farm_id: null, case_type: 'manual', title: '', summary: '',
    priority: 'P2', severity: 'medium',
  }
  showCreate.value = true
}

async function submitCreate() {
  try {
    const created = await store.createCase(createForm.value)
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã tạo case ${created.case_no}`, life: 3000 })
    showCreate.value = false
    loadData()
  } catch (e) {
    const msg = e.response?.data?.error?.message || 'Có lỗi xảy ra'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 5000 })
  }
}

onMounted(async () => {
  await farmStore.fetchFarms()
  await loadData()
})
</script>

<template>
  <Toast />
  <div class="case-queue-page">
    <div class="page-header">
      <div>
        <h2><i class="pi pi-exclamation-triangle" style="color: var(--p-orange-500)"></i> Case Review Queue</h2>
        <p class="subtitle">Danh sách case rủi ro — chuyên gia xử lý theo mức ưu tiên và SLA</p>
      </div>
      <div class="header-actions">
        <div class="view-toggle">
          <Button :label="'Queue'" :severity="viewMode === 'queue' ? undefined : 'secondary'" size="small" @click="switchView('queue')" />
          <Button :label="'Tất cả'" :severity="viewMode === 'all' ? undefined : 'secondary'" size="small" @click="switchView('all')" />
        </div>
        <Button
          v-if="authStore.hasPermission('CASE_CREATE')"
          label="Tạo Case"
          icon="pi pi-plus"
          @click="openCreate"
        />
      </div>
    </div>

    <!-- Filters (only for "all" mode) -->
    <div class="filter-bar" v-if="viewMode === 'all'">
      <Select v-model="store.filters.farm_id" :options="farmOptions" optionLabel="label" optionValue="value" placeholder="Trại" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.priority" :options="priorityOptions" optionLabel="label" optionValue="value" placeholder="Mức ưu tiên" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.current_status" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Trạng thái" class="filter-select" @change="onFilter" />
      <Select v-model="store.filters.case_type" :options="caseTypeOptions" optionLabel="label" optionValue="value" placeholder="Loại case" class="filter-select" @change="onFilter" />
    </div>

    <!-- Main layout: Queue table + Quick preview -->
    <div class="queue-layout">
      <!-- Table -->
      <div class="queue-table-wrap">
        <DataTable
          :value="tableData"
          :loading="tableLoading"
          :lazy="true"
          :paginator="true"
          :rows="20"
          :totalRecords="tableTotal"
          :first="viewMode === 'queue' ? (store.queuePage - 1) * 20 : (store.filters.page - 1) * store.filters.page_size"
          @page="onPage"
          selectionMode="single"
          v-model:selection="selectedCase"
          @rowSelect="onRowSelect"
          stripedRows
          class="case-table"
        >
          <Column header="Case No" style="width: 120px">
            <template #body="{ data }">
              <a class="case-link" @click.prevent="openDetail(data)">{{ data.case_no }}</a>
            </template>
          </Column>
          <Column header="Trại" style="width: 120px">
            <template #body="{ data }">{{ farmName(data.farm_id) }}</template>
          </Column>
          <Column header="Loại" style="width: 110px">
            <template #body="{ data }">
              <Tag :value="caseTypeLabel(data.case_type)" severity="secondary" />
            </template>
          </Column>
          <Column header="Ưu tiên" style="width: 90px">
            <template #body="{ data }">
              <Tag :value="data.priority" :severity="priorityColor(data.priority)" />
            </template>
          </Column>
          <Column header="Nghiêm trọng" style="width: 110px">
            <template #body="{ data }">
              <Tag :value="data.severity" :severity="severityColor(data.severity)" />
            </template>
          </Column>
          <Column header="Tiêu đề" style="min-width: 180px">
            <template #body="{ data }">
              <div class="title-cell">{{ data.title }}</div>
            </template>
          </Column>
          <Column header="Hạn SLA" style="width: 90px">
            <template #body="{ data }">
              <span :class="{ overdue: data.first_response_due_at && new Date(data.first_response_due_at) < new Date() }">
                {{ formatShortDate(data.first_response_due_at) }}
              </span>
            </template>
          </Column>
          <Column header="Trạng thái" style="width: 120px">
            <template #body="{ data }">
              <Tag :value="statusLabel(data.current_status)" :severity="statusColor(data.current_status)" />
            </template>
          </Column>
          <template #empty>
            <div class="empty-msg">Chưa có case nào trong hàng đợi.</div>
          </template>
        </DataTable>
      </div>

      <!-- Quick preview panel -->
      <div class="quick-preview" v-if="selectedCase">
        <h4>{{ selectedCase.case_no }}</h4>
        <div class="preview-field">
          <label>Tiêu đề</label>
          <span>{{ selectedCase.title }}</span>
        </div>
        <div class="preview-field">
          <label>Mô tả</label>
          <span>{{ selectedCase.summary || '—' }}</span>
        </div>
        <div class="preview-field">
          <label>Trại</label>
          <span>{{ farmName(selectedCase.farm_id) }}</span>
        </div>
        <div class="preview-row">
          <div class="preview-field">
            <label>Ưu tiên</label>
            <Tag :value="selectedCase.priority" :severity="priorityColor(selectedCase.priority)" />
          </div>
          <div class="preview-field">
            <label>Nghiêm trọng</label>
            <Tag :value="selectedCase.severity" :severity="severityColor(selectedCase.severity)" />
          </div>
        </div>
        <div class="preview-field">
          <label>Trạng thái</label>
          <Tag :value="statusLabel(selectedCase.current_status)" :severity="statusColor(selectedCase.current_status)" />
        </div>
        <div class="preview-field">
          <label>Ngày mở</label>
          <span>{{ formatDate(selectedCase.opened_at) }}</span>
        </div>
        <Button label="Mở chi tiết" icon="pi pi-arrow-right" class="mt-3 w-full" @click="openDetail(selectedCase)" />
      </div>
    </div>

    <!-- Create Case Dialog -->
    <Dialog v-model:visible="showCreate" header="Tạo Case rủi ro mới" modal :style="{ width: '560px' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Trại <span class="req">*</span></label>
          <Select v-model="createForm.farm_id" :options="farmStore.farms" optionLabel="name" optionValue="id" placeholder="Chọn trại" class="w-full" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Loại case</label>
            <Select v-model="createForm.case_type" :options="caseTypeOptions.filter(o => o.value)" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="form-field">
            <label>Mức ưu tiên</label>
            <Select v-model="createForm.priority" :options="priorityOptions.filter(o => o.value)" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="form-field">
          <label>Mức nghiêm trọng</label>
          <Select v-model="createForm.severity" :options="severityCreateOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="form-field">
          <label>Tiêu đề <span class="req">*</span></label>
          <InputText v-model="createForm.title" placeholder="Mô tả ngắn gọn vấn đề" class="w-full" />
        </div>
        <div class="form-field">
          <label>Tóm tắt</label>
          <Textarea v-model="createForm.summary" rows="3" placeholder="Bối cảnh và lý do mở case..." class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showCreate = false" />
        <Button label="Tạo Case" icon="pi pi-plus" @click="submitCreate" :disabled="!createForm.farm_id || !createForm.title" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.case-queue-page { max-width: 1400px; }

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;
}
.page-header h2 {
  margin: 0 0 0.25rem; display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;
}
.subtitle { font-size: 0.85rem; color: var(--p-text-muted-color); margin: 0; }

.header-actions { display: flex; gap: 0.75rem; align-items: center; }
.view-toggle { display: flex; gap: 0.25rem; }

.filter-bar { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.filter-select { min-width: 160px; }

.queue-layout { display: flex; gap: 1rem; align-items: flex-start; }
.queue-table-wrap { flex: 1; min-width: 0; }

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

.case-link { color: var(--p-primary-color); cursor: pointer; font-weight: 600; text-decoration: underline; }
.case-link:hover { text-decoration: none; }

.title-cell { font-size: 0.85rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

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
