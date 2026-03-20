<script setup>
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
import Textarea from 'primevue/textarea'
import { useKillerMetricStore } from '@/stores/killerMetric.js'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const toast = useToast()
const store = useKillerMetricStore()
const farmStore = useFarmStore()
const authStore = useAuthStore()

const statusOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Open', value: 'open' },
  { label: 'Under Review', value: 'under_review' },
  { label: 'Contained', value: 'contained' },
  { label: 'Closed', value: 'closed' },
]

const farmOptions = computed(() => [
  { label: 'Tất cả trại', value: null },
  ...farmStore.farms.map(f => ({ label: f.name, value: f.id })),
])

const definitionOptions = computed(() => [
  { label: 'Tất cả loại', value: null },
  ...store.definitions.map(d => ({ label: d.name, value: d.id })),
])

// ── Create event dialog ──
const showCreate = ref(false)
const createForm = ref({ farm_id: null, definition_id: null, summary: '', source_type: 'field_report' })

const sourceOptions = [
  { label: 'Báo cáo thực địa', value: 'field_report' },
  { label: 'Camera giám sát', value: 'camera' },
  { label: 'Đánh giá', value: 'assessment' },
  { label: 'Khác', value: 'other' },
]

// ── Status transition dialog ──
const showTransition = ref(false)
const transitionEvent = ref(null)
const transitionTarget = ref(null)

const VALID_TRANSITIONS = {
  open: ['under_review'],
  under_review: ['contained', 'open'],
  contained: ['closed', 'under_review'],
}

function statusColor(status) {
  const m = { open: 'danger', under_review: 'warn', contained: 'info', closed: 'success' }
  return m[status] || 'secondary'
}

function statusLabel(status) {
  const m = { open: 'Open', under_review: 'Đang xem xét', contained: 'Đã kiểm soát', closed: 'Đã đóng' }
  return m[status] || status
}

function severityColor(level) {
  const m = { critical: 'danger', high: 'warn', medium: 'info' }
  return m[level] || 'secondary'
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function nextActions(status) {
  return VALID_TRANSITIONS[status] || []
}

function openTransition(event, target) {
  transitionEvent.value = event
  transitionTarget.value = target
  showTransition.value = true
}

async function confirmTransition() {
  try {
    await store.updateEvent(transitionEvent.value.id, {
      status: transitionTarget.value,
      version: transitionEvent.value.version,
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã chuyển sang ${statusLabel(transitionTarget.value)}`, life: 3000 })
    showTransition.value = false
    await store.fetchEvents()
  } catch (e) {
    const msg = e.response?.data?.error?.message || 'Có lỗi xảy ra'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 5000 })
  }
}

function openCreate() {
  createForm.value = { farm_id: null, definition_id: null, summary: '', source_type: 'field_report' }
  showCreate.value = true
}

async function submitCreate() {
  try {
    await store.createEvent(createForm.value)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã ghi nhận sự kiện killer metric', life: 3000 })
    showCreate.value = false
    await store.fetchEvents()
  } catch (e) {
    const msg = e.response?.data?.error?.message || 'Có lỗi xảy ra'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 5000 })
  }
}

function onFilter() {
  store.filters.page = 1
  store.fetchEvents()
}

function onPage(e) {
  store.filters.page = e.page + 1
  store.filters.page_size = e.rows
  store.fetchEvents()
}

onMounted(async () => {
  await Promise.all([
    store.fetchDefinitions(),
    farmStore.fetchFarms(),
    store.fetchEvents(),
  ])
})
</script>

<template>
  <Toast />
  <div class="km-event-page">
    <div class="page-header">
      <div>
        <h2><i class="pi pi-bolt" style="color: var(--p-red-500)"></i> Killer Metric Events</h2>
        <p class="subtitle">Danh sách sự kiện vi phạm nghiêm trọng — quản lý trạng thái và case</p>
      </div>
      <Button
        v-if="authStore.hasPermission('KILLER_EVENT_WRITE')"
        label="Ghi nhận sự kiện"
        icon="pi pi-plus"
        severity="danger"
        @click="openCreate"
      />
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <Select
        v-model="store.filters.farm_id"
        :options="farmOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Trại"
        class="filter-select"
        @change="onFilter"
      />
      <Select
        v-model="store.filters.status"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Trạng thái"
        class="filter-select"
        @change="onFilter"
      />
      <Select
        v-model="store.filters.definition_id"
        :options="definitionOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Loại"
        class="filter-select"
        @change="onFilter"
      />
    </div>

    <!-- Events table -->
    <DataTable
      :value="store.events"
      :loading="store.eventsLoading"
      :lazy="true"
      :paginator="true"
      :rows="store.filters.page_size"
      :totalRecords="store.totalRecords"
      :first="(store.filters.page - 1) * store.filters.page_size"
      @page="onPage"
      stripedRows
      class="event-table"
    >
      <Column header="Loại vi phạm" style="min-width: 180px">
        <template #body="{ data }">
          <div class="def-cell">
            <Tag :value="data.definition?.severity_level" :severity="severityColor(data.definition?.severity_level)" class="sev-tag" />
            <div>
              <div class="def-name">{{ data.definition?.name || '—' }}</div>
              <div class="def-code">{{ data.definition?.code }}</div>
            </div>
          </div>
        </template>
      </Column>
      <Column header="Trại" style="width: 140px">
        <template #body="{ data }">
          {{ farmStore.farms.find(f => f.id === data.farm_id)?.name || data.farm_id?.slice(0, 8) }}
        </template>
      </Column>
      <Column header="Mô tả" style="min-width: 200px">
        <template #body="{ data }">
          <div class="summary-text">{{ data.summary }}</div>
        </template>
      </Column>
      <Column header="Thời gian" style="width: 150px">
        <template #body="{ data }">
          {{ formatDate(data.event_at) }}
        </template>
      </Column>
      <Column header="Trạng thái" style="width: 140px">
        <template #body="{ data }">
          <Tag :value="statusLabel(data.status)" :severity="statusColor(data.status)" />
        </template>
      </Column>
      <Column header="Hành động" style="width: 200px">
        <template #body="{ data }">
          <div class="action-btns">
            <Button
              icon="pi pi-eye"
              size="small"
              severity="info"
              outlined
              v-tooltip.top="'Chi tiết'"
              @click="router.push(`/killer-metrics/events/${data.id}`)"
            />
            <template v-if="data.status !== 'closed'">
              <Button
                v-for="target in nextActions(data.status)"
                :key="target"
                :label="statusLabel(target)"
                size="small"
                :severity="statusColor(target)"
                outlined
                @click="openTransition(data, target)"
              />
            </template>
            <Tag v-else value="Đã đóng" severity="success" />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="empty-msg">Chưa có sự kiện killer metric nào.</div>
      </template>
    </DataTable>

    <!-- Create Event Dialog -->
    <Dialog v-model:visible="showCreate" header="Ghi nhận sự kiện Killer Metric" modal :style="{ width: '520px' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Trại</label>
          <Select v-model="createForm.farm_id" :options="farmStore.farms" optionLabel="name" optionValue="id" placeholder="Chọn trại" class="w-full" />
        </div>
        <div class="form-field">
          <label>Loại vi phạm</label>
          <Select v-model="createForm.definition_id" :options="store.definitions" optionLabel="name" optionValue="id" placeholder="Chọn loại" class="w-full" />
        </div>
        <div class="form-field">
          <label>Nguồn</label>
          <Select v-model="createForm.source_type" :options="sourceOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="form-field">
          <label>Mô tả</label>
          <Textarea v-model="createForm.summary" rows="3" placeholder="Mô tả chi tiết sự kiện..." class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showCreate = false" />
        <Button label="Ghi nhận" icon="pi pi-check" severity="danger" @click="submitCreate" :disabled="!createForm.farm_id || !createForm.definition_id || !createForm.summary" />
      </template>
    </Dialog>

    <!-- Transition Confirm Dialog -->
    <Dialog v-model:visible="showTransition" header="Xác nhận chuyển trạng thái" modal :style="{ width: '420px' }">
      <p v-if="transitionEvent">
        Chuyển sự kiện <strong>{{ transitionEvent.definition?.name }}</strong>
        từ <Tag :value="statusLabel(transitionEvent.status)" :severity="statusColor(transitionEvent.status)" />
        sang <Tag :value="statusLabel(transitionTarget)" :severity="statusColor(transitionTarget)" /> ?
      </p>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showTransition = false" />
        <Button label="Xác nhận" icon="pi pi-check" @click="confirmTransition" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.km-event-page { width: 100%; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h2 {
  margin: 0 0 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.3rem;
}

.subtitle {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin: 0;
}

.filter-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-select { min-width: 180px; }

.def-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sev-tag { font-size: 0.7rem; }

.def-name { font-weight: 600; font-size: 0.85rem; }
.def-code { font-size: 0.75rem; color: var(--p-text-muted-color); }

.summary-text {
  font-size: 0.85rem;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-btns { display: flex; gap: 0.35rem; flex-wrap: wrap; }

.empty-msg {
  text-align: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-field label {
  font-weight: 600;
  font-size: 0.85rem;
}

.w-full { width: 100%; }
</style>
