<script setup>
import { ref, onMounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Toast from 'primevue/toast'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import StatusBadge from '@/components/common/StatusBadge.vue'
import FloorplanCanvas from '@/components/scars/FloorplanCanvas.vue'
import ScarDetailDrawer from '@/components/scars/ScarDetailDrawer.vue'
import ScarFormDialog from '@/components/scars/ScarFormDialog.vue'
import * as scarService from '@/services/scarService.js'
import * as farmService from '@/services/farmService.js'

const toast = useToast()

// ── Data ──────────────────────────────────────────────────────
const farms = ref([])
const scarMapData = ref({ floorplan: null, markers: [], scars: [] })
const scarList = ref([])
const scarListTotal = ref(0)
const loading = ref(false)
const loadingList = ref(false)

// ── Filters ───────────────────────────────────────────────────
const selectedFarmId = ref(null)
const filterScarType = ref(null)
const filterConfidence = ref(null)
const filterDateRange = ref(null)

const scarTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Ổ dịch', value: 'outbreak' },
  { label: 'Hotspot', value: 'hotspot' },
  { label: 'Vi phạm lặp lại', value: 'repeated_breach' },
  { label: 'Suýt xảy ra', value: 'near_miss' },
  { label: 'Lỗi cấu trúc', value: 'structural_flaw' },
]

const confidenceOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Nghi ngờ', value: 'suspected' },
  { label: 'Có thể', value: 'probable' },
  { label: 'Xác nhận', value: 'confirmed' },
]

const scarTypeLabels = {
  outbreak: 'Ổ dịch',
  hotspot: 'Hotspot',
  repeated_breach: 'Vi phạm lặp lại',
  near_miss: 'Suýt xảy ra',
  structural_flaw: 'Lỗi cấu trúc',
}

const scarTypeSeverity = {
  outbreak: 'danger',
  hotspot: 'warn',
  repeated_breach: 'warn',
  near_miss: 'info',
  structural_flaw: 'secondary',
}

// ── Drawer ────────────────────────────────────────────────────
const drawerVisible = ref(false)
const selectedScarId = ref(null)
// ── Create/Edit dialog ───────────────────────────────────────────
const formDialogVisible = ref(false)
const editingScar = ref(null)
// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  try {
    const result = await farmService.listFarms({ page_size: 100 })
    farms.value = result.data || []
    if (farms.value.length > 0) {
      selectedFarmId.value = farms.value[0].id
    }
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải danh sách trại', life: 3000 })
  }
})

watch([selectedFarmId, filterScarType, filterConfidence, filterDateRange], () => {
  if (selectedFarmId.value) {
    loadScarMap()
    loadScarList()
  }
}, { immediate: true })

async function loadScarMap() {
  if (!selectedFarmId.value) return
  loading.value = true
  try {
    const params = {}
    if (filterScarType.value) params.scar_type = filterScarType.value
    if (filterConfidence.value) params.confidence_level = filterConfidence.value
    if (filterDateRange.value?.[0]) params.date_from = formatDateISO(filterDateRange.value[0])
    if (filterDateRange.value?.[1]) params.date_to = formatDateISO(filterDateRange.value[1])

    scarMapData.value = await scarService.getScarMap(selectedFarmId.value, params)
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải scar map', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function loadScarList() {
  if (!selectedFarmId.value) return
  loadingList.value = true
  try {
    const params = { farm_id: selectedFarmId.value, page_size: 50 }
    if (filterScarType.value) params.scar_type = filterScarType.value
    if (filterConfidence.value) params.confidence_level = filterConfidence.value

    const result = await scarService.listScars(params)
    scarList.value = result.data || []
    scarListTotal.value = result.meta?.total || 0
  } catch {
    // silent — map is primary
  } finally {
    loadingList.value = false
  }
}

function onScarClick(scar) {
  selectedScarId.value = scar.id
  drawerVisible.value = true
}

function onScarValidated() {
  loadScarMap()
  loadScarList()
}

function onScarUpdated() {
  loadScarMap()
  loadScarList()
}

function openCreateDialog() {
  editingScar.value = null
  formDialogVisible.value = true
}

function onEditScar(scar) {
  editingScar.value = scar
  drawerVisible.value = false
  formDialogVisible.value = true
}

function onScarSaved() {
  loadScarMap()
  loadScarList()
}

function onRowSelect(event) {
  selectedScarId.value = event.data.id
  drawerVisible.value = true
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('vi-VN')
}

function formatDateISO(d) {
  if (!d) return null
  return d instanceof Date ? d.toISOString().split('T')[0] : d
}

function selectedFarmName() {
  const f = farms.value.find(f => f.id === selectedFarmId.value)
  return f ? f.name : ''
}
</script>

<template>
  <Toast />
  <div class="scar-map-view">
    <!-- Page header -->
    <div class="page-header">
      <h2>Scar Map</h2>
      <span class="page-subtitle" v-if="selectedFarmId">{{ selectedFarmName() }}</span>
      <Button v-if="selectedFarmId" label="Tạo Scar" icon="pi pi-plus" size="small" @click="openCreateDialog" class="ml-auto" />
    </div>

    <!-- Filters bar -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>Trại</label>
        <Select
          v-model="selectedFarmId"
          :options="farms"
          optionLabel="name"
          optionValue="id"
          placeholder="Chọn trại"
          class="filter-select"
          filter
        />
      </div>
      <div class="filter-item">
        <label>Loại scar</label>
        <Select
          v-model="filterScarType"
          :options="scarTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Tất cả"
          class="filter-select"
        />
      </div>
      <div class="filter-item">
        <label>Độ tin cậy</label>
        <Select
          v-model="filterConfidence"
          :options="confidenceOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Tất cả"
          class="filter-select"
        />
      </div>
      <div class="filter-item">
        <label>Khoảng ngày</label>
        <DatePicker
          v-model="filterDateRange"
          selectionMode="range"
          dateFormat="dd/mm/yy"
          placeholder="Từ — Đến"
          class="filter-select"
          :manualInput="false"
          showButtonBar
        />
      </div>
    </div>

    <!-- Main content: Canvas + Scar list -->
    <div class="map-content" v-if="selectedFarmId">
      <!-- Canvas section -->
      <div class="canvas-section">
        <div class="canvas-header" v-if="scarMapData.floorplan">
          <span class="floorplan-title">
            <i class="pi pi-map"></i>
            {{ scarMapData.floorplan.title }} (v{{ scarMapData.floorplan.version_no }})
          </span>
          <Tag :value="scarMapData.floorplan.status" :severity="scarMapData.floorplan.status === 'active' ? 'success' : 'secondary'" />
        </div>
        <div class="canvas-header" v-else>
          <span class="floorplan-title text-muted">Chưa có floorplan active cho trại này</span>
        </div>

        <FloorplanCanvas
          :markers="scarMapData.markers || []"
          :scars="scarMapData.scars || []"
          :readonly="true"
          @scarClick="onScarClick"
        />
      </div>

      <!-- Scar list strip -->
      <div class="scar-list-section">
        <h3>Danh sách Scar ({{ scarListTotal }})</h3>
        <DataTable
          :value="scarList"
          :loading="loadingList"
          stripedRows
          size="small"
          selectionMode="single"
          @rowSelect="onRowSelect"
          :paginator="false"
          scrollable
          scrollHeight="300px"
        >
          <template #empty>Không có scar nào phù hợp.</template>
          <Column field="scar_type" header="Loại" style="width: 140px">
            <template #body="{ data }">
              <Tag :value="scarTypeLabels[data.scar_type] || data.scar_type" :severity="scarTypeSeverity[data.scar_type] || 'info'" />
            </template>
          </Column>
          <Column field="title" header="Tiêu đề" />
          <Column field="confidence_level" header="Độ tin cậy" style="width: 110px">
            <template #body="{ data }">
              <StatusBadge :value="data.confidence_level" type="confidence" />
            </template>
          </Column>
          <Column field="event_date" header="Ngày" style="width: 100px">
            <template #body="{ data }">{{ formatDate(data.event_date) }}</template>
          </Column>
          <Column field="recurrence_count" header="Lặp" style="width: 60px; text-align: center">
            <template #body="{ data }">
              <Tag v-if="data.recurrence_flag" :value="String(data.recurrence_count)" severity="warn" rounded />
              <span v-else>—</span>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-map" style="font-size: 3rem; opacity: 0.3"></i>
      <p>Chọn trại để xem Scar Map</p>
    </div>

    <!-- Detail drawer -->
    <ScarDetailDrawer
      v-model:visible="drawerVisible"
      :scarId="selectedScarId"
      :farmId="selectedFarmId"
      @validated="onScarValidated"
      @edit="onEditScar"
      @updated="onScarUpdated"
    />

    <!-- Create/Edit dialog -->
    <ScarFormDialog
      v-model:visible="formDialogVisible"
      :scar="editingScar"
      :farmId="selectedFarmId"
      :farms="farms"
      @saved="onScarSaved"
    />
  </div>
</template>

<style scoped>
.scar-map-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.page-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}
.page-header h2 {
  margin: 0;
}
.page-subtitle {
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}
.ml-auto {
  margin-left: auto;
}

/* ── Filter bar ──────────────────────────────────────── */
.filter-bar {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: flex-end;
  padding: 0.75rem 1rem;
  background: var(--p-surface-50);
  border: 1px solid var(--p-surface-200);
  border-radius: var(--p-border-radius);
}
.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 160px;
}
.filter-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
}
.filter-select {
  width: 100%;
}

/* ── Map content ─────────────────────────────────────── */
.map-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.canvas-section {
  background: var(--p-content-background);
  border: 1px solid var(--p-surface-200);
  border-radius: var(--p-border-radius);
  padding: 1rem;
}
.canvas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.floorplan-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}
.text-muted {
  color: var(--p-text-muted-color);
  font-weight: normal;
}

/* ── Scar list ───────────────────────────────────────── */
.scar-list-section {
  background: var(--p-content-background);
  border: 1px solid var(--p-surface-200);
  border-radius: var(--p-border-radius);
  padding: 1rem;
}
.scar-list-section h3 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}

/* ── Empty state ─────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--p-text-muted-color);
  gap: 1rem;
}
</style>
