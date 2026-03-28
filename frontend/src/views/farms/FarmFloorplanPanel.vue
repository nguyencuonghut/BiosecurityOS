<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import ProgressBar from 'primevue/progressbar'
import { useAuthStore } from '@/stores/auth.js'
import { useFarmStore } from '@/stores/farm.js'
import * as floorplanService from '@/services/floorplanService.js'
import * as attachmentService from '@/services/attachmentService.js'
import FloorplanCanvas from '@/components/scars/FloorplanCanvas.vue'

const props = defineProps({
  farmId: { type: String, required: true },
})

const toast = useToast()
const authStore = useAuthStore()
const farmStore = useFarmStore()

const floorplans = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const uploadProgress = ref(0)
const selectedFile = ref(null)
const fileInputRef = ref(null)
const previewUrls = ref({})

// Canvas state
const activeFloorplanId = ref(null)
const canvasMarkers = ref([])
const canvasImageUrl = ref(null)
const showPlaceDialog = ref(false)
const placingCoords = ref(null)
const placeForm = ref({ area_id: null })

const ALLOWED_MIME = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
const MAX_SIZE = 50 * 1024 * 1024

const form = ref({
  title: '',
  effective_from: null,
})

// Active floorplan (status = active)
const activeFloorplan = computed(() => floorplans.value.find(fp => fp.status === 'active'))

// Areas not yet placed on the active floorplan (available for placement)
const unplacedAreas = computed(() => {
  const placedAreaIds = new Set(canvasMarkers.value.filter(m => m.area_id).map(m => m.area_id))
  return farmStore.areas.filter(a => a.is_active && !placedAreaIds.has(a.id))
})



const areaTypeMap = computed(() => {
  const map = {}
  for (const t of farmStore.areaTypes) map[t.id] = t.name
  return map
})

const areaTypeCodeMap = computed(() => {
  const map = {}
  for (const t of farmStore.areaTypes) map[t.id] = t.code
  return map
})

onMounted(async () => {
  await fetchFloorplans()
  // Ensure areas, routes and area types are loaded
  if (!farmStore.areas.length) await farmStore.fetchAreas(props.farmId)
  if (!farmStore.routes.length) await farmStore.fetchRoutes(props.farmId)
  if (!farmStore.areaTypes.length) await farmStore.fetchAreaTypes()
})

async function fetchFloorplans() {
  loading.value = true
  try {
    floorplans.value = await floorplanService.listFloorplans(props.farmId)
    // Load preview URLs for floorplans that have images
    for (const fp of floorplans.value) {
      if (fp.plan_file_attachment_id && !previewUrls.value[fp.id]) {
        loadPreview(fp)
      }
    }
    // Auto-load active floorplan canvas
    const active = activeFloorplan.value
    if (active) {
      await loadCanvasData(active)
    }
  } finally {
    loading.value = false
  }
}

async function loadPreview(fp) {
  try {
    const result = await attachmentService.getViewUrl(fp.plan_file_attachment_id)
    previewUrls.value[fp.id] = result.view_url
  } catch {
    // ignore — no preview available
  }
}

function openCreate() {
  form.value = { title: '', effective_from: null }
  selectedFile.value = null
  uploadProgress.value = 0
  showCreateDialog.value = true
}

function onFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!ALLOWED_MIME.includes(file.type)) {
    toast.add({ severity: 'warn', summary: 'Lỗi', detail: 'Chỉ hỗ trợ PNG, JPEG, WebP, SVG', life: 4000 })
    return
  }
  if (file.size > MAX_SIZE) {
    toast.add({ severity: 'warn', summary: 'Lỗi', detail: 'File quá lớn (tối đa 50MB)', life: 4000 })
    return
  }
  selectedFile.value = file
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function submitCreate() {
  if (!form.value.title || !form.value.effective_from) return
  creating.value = true
  uploadProgress.value = 0
  try {
    let attachmentId = null

    // Upload image if selected
    if (selectedFile.value) {
      const attachment = await attachmentService.uploadFile(
        selectedFile.value,
        'floorplan_version',
        props.farmId,
        (pct) => { uploadProgress.value = pct },
      )
      attachmentId = attachment.id
    }

    const effectiveFrom = form.value.effective_from instanceof Date
      ? form.value.effective_from.toISOString().split('T')[0]
      : form.value.effective_from
    await floorplanService.createFloorplan(props.farmId, {
      title: form.value.title,
      effective_from: effectiveFrom,
      plan_file_attachment_id: attachmentId,
    })
    showCreateDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo floorplan mới', life: 3000 })
    await fetchFloorplans()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể tạo', life: 4000 })
  } finally {
    creating.value = false
  }
}

async function approveFloorplan(fp) {
  try {
    await floorplanService.approveFloorplan(fp.id)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã kích hoạt floorplan', life: 3000 })
    await fetchFloorplans()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể kích hoạt', life: 4000 })
  }
}

function statusSeverity(status) {
  return { draft: 'warn', active: 'success', archived: 'secondary' }[status] || 'info'
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('vi-VN')
}

// ── Canvas: load floorplan markers + image ────────────────────
async function loadCanvasData(fp) {
  activeFloorplanId.value = fp.id
  try {
    const markers = await floorplanService.listMarkers(fp.id)
    canvasMarkers.value = markers
  } catch {
    canvasMarkers.value = []
  }
  // Load image
  if (fp.plan_file_attachment_id) {
    try {
      const result = await attachmentService.getViewUrl(fp.plan_file_attachment_id)
      canvasImageUrl.value = result.view_url
    } catch {
      canvasImageUrl.value = null
    }
  } else {
    canvasImageUrl.value = null
  }
}

// Click on canvas → open dialog to place an area marker
function onCanvasClick(coords) {
  if (!unplacedAreas.value.length) {
    toast.add({ severity: 'info', summary: 'Thông tin', detail: 'Tất cả khu vực đã được đặt trên sơ đồ', life: 3000 })
    return
  }
  placingCoords.value = coords
  placeForm.value = { area_id: null }
  showPlaceDialog.value = true
}

// Submit: create marker for an area
async function submitPlaceMarker() {
  if (!placeForm.value.area_id || !placingCoords.value) return
  const area = farmStore.areas.find(a => a.id === placeForm.value.area_id)
  if (!area) return
  try {
    await floorplanService.createMarker(activeFloorplanId.value, {
      area_id: area.id,
      marker_type: (area.area_type_id && areaTypeCodeMap.value[area.area_type_id]) || 'other',
      label: area.name,
      x_percent: placingCoords.value.x_percent,
      y_percent: placingCoords.value.y_percent,
    })
    showPlaceDialog.value = false
    toast.add({ severity: 'success', summary: 'Đã đặt', detail: `${area.name} đã được gắn lên sơ đồ`, life: 3000 })
    // Reload markers
    const markers = await floorplanService.listMarkers(activeFloorplanId.value)
    canvasMarkers.value = markers
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể đặt marker', life: 4000 })
  }
}

// Delete a marker (click on marker → confirm remove)
async function onMarkerClick(marker) {
  if (!authStore.hasPermission('SCAR_WRITE')) return
  if (!confirm(`Bỏ "${marker.label}" khỏi sơ đồ?`)) return
  try {
    await floorplanService.deleteMarker(activeFloorplanId.value, marker.id)
    canvasMarkers.value = canvasMarkers.value.filter(m => m.id !== marker.id)
    toast.add({ severity: 'info', summary: 'Đã gỡ', detail: `${marker.label} đã được gỡ khỏi sơ đồ`, life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể gỡ marker', life: 4000 })
  }
}

// Drag marker to new position
async function onMarkerDragEnd({ id, x_percent, y_percent }) {
  if (!activeFloorplanId.value) return
  try {
    await floorplanService.updateMarker(activeFloorplanId.value, id, { x_percent, y_percent })
    const idx = canvasMarkers.value.findIndex(m => m.id === id)
    if (idx !== -1) {
      canvasMarkers.value[idx] = { ...canvasMarkers.value[idx], x_percent, y_percent }
    }
    toast.add({ severity: 'success', summary: 'Đã di chuyển', detail: 'Vị trí marker đã được cập nhật', life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể cập nhật vị trí marker', life: 4000 })
    // Reload to revert
    const markers = await floorplanService.listMarkers(activeFloorplanId.value)
    canvasMarkers.value = markers
  }
}

function areaOptionLabel(area) {
  const typeName = area.area_type_id ? areaTypeMap.value[area.area_type_id] : null
  return typeName ? `${area.name} (${typeName})` : area.name
}
</script>

<template>
  <div class="floorplan-panel">
    <!-- Interactive Canvas for Active Floorplan -->
    <div v-if="activeFloorplan" class="canvas-section">
      <div class="panel-toolbar">
        <h3>
          <i class="pi pi-map" /> Sơ đồ mặt bằng — {{ activeFloorplan.title }}
          <Tag :value="'v' + activeFloorplan.version_no" severity="info" rounded />
        </h3>
        <div class="toolbar-actions">
          <span v-if="unplacedAreas.length" class="unplaced-hint">
            <i class="pi pi-info-circle" /> Click vào sơ đồ để đặt khu vực ({{ unplacedAreas.length }} chưa đặt)
          </span>
        </div>
      </div>
      <FloorplanCanvas
        :markers="canvasMarkers"
        :routes="farmStore.routes"
        :imageUrl="canvasImageUrl"
        :readonly="!authStore.hasPermission('SCAR_WRITE')"
        @canvasClick="onCanvasClick"
        @markerClick="onMarkerClick"
        @markerDragEnd="onMarkerDragEnd"
      />
    </div>

    <!-- Floorplan Versions Table -->
    <div class="panel-toolbar">
      <h3>Danh sách Floorplan</h3>
      <Button
        v-if="authStore.hasPermission('SCAR_WRITE')"
        label="Tạo phiên bản"
        icon="pi pi-plus"
        size="small"
        @click="openCreate"
      />
    </div>

    <DataTable :value="floorplans" :loading="loading" stripedRows size="small" :paginator="false">
      <template #empty>Chưa có floorplan nào.</template>
      <Column header="Ảnh" style="width: 80px">
        <template #body="{ data }">
          <img
            v-if="previewUrls[data.id]"
            :src="previewUrls[data.id]"
            class="floorplan-thumb"
            alt="Floorplan"
          />
          <span v-else class="thumb-placeholder"><i class="pi pi-image" /></span>
        </template>
      </Column>
      <Column field="version_no" header="Phiên bản" style="width: 80px">
        <template #body="{ data }">v{{ data.version_no }}</template>
      </Column>
      <Column field="title" header="Tiêu đề" />
      <Column field="status" header="Trạng thái" style="width: 120px">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity(data.status)" />
        </template>
      </Column>
      <Column field="effective_from" header="Hiệu lực từ" style="width: 130px">
        <template #body="{ data }">{{ formatDate(data.effective_from) }}</template>
      </Column>
      <Column field="effective_to" header="Hiệu lực đến" style="width: 130px">
        <template #body="{ data }">{{ formatDate(data.effective_to) }}</template>
      </Column>
      <Column header="" style="width: 130px">
        <template #body="{ data }">
          <Button
            v-if="data.status === 'draft' && authStore.hasPermission('SCAR_WRITE')"
            label="Kích hoạt"
            icon="pi pi-check"
            size="small"
            severity="success"
            text
            @click="approveFloorplan(data)"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Create dialog -->
    <Dialog v-model:visible="showCreateDialog" header="Tạo Floorplan mới" modal :style="{ width: '32rem' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Tiêu đề *</label>
          <InputText v-model="form.title" class="w-full" placeholder="VD: Mặt bằng v2 — cải tạo 2026" />
        </div>
        <div class="form-field">
          <label>Hiệu lực từ *</label>
          <DatePicker v-model="form.effective_from" dateFormat="dd/mm/yy" class="w-full" />
        </div>
        <div class="form-field">
          <label>Ảnh sơ đồ mặt bằng</label>
          <div class="file-upload-area" @click="triggerFileInput">
            <input
              ref="fileInputRef"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              style="display: none"
              @change="onFileSelect"
            />
            <div v-if="!selectedFile" class="upload-placeholder">
              <i class="pi pi-cloud-upload" />
              <span>Click để chọn ảnh (PNG, JPEG, WebP, SVG)</span>
            </div>
            <div v-else class="upload-selected">
              <i class="pi pi-image" />
              <span>{{ selectedFile.name }}</span>
              <span class="file-size">({{ (selectedFile.size / 1024).toFixed(0) }} KB)</span>
            </div>
          </div>
          <ProgressBar v-if="creating && uploadProgress > 0 && uploadProgress < 100" :value="uploadProgress" style="height: 6px; margin-top: 0.5rem" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showCreateDialog = false" />
        <Button label="Tạo" icon="pi pi-check" :loading="creating" @click="submitCreate" :disabled="!form.title || !form.effective_from" />
      </template>
    </Dialog>

    <!-- Place area marker dialog -->
    <Dialog v-model:visible="showPlaceDialog" header="Đặt khu vực lên sơ đồ" modal :style="{ width: '28rem' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Chọn khu vực *</label>
          <Select
            v-model="placeForm.area_id"
            :options="unplacedAreas"
            optionValue="id"
            :optionLabel="areaOptionLabel"
            placeholder="Chọn khu vực..."
            class="w-full"
            filter
          />
        </div>
        <div v-if="placingCoords" class="coords-preview">
          <i class="pi pi-map-marker" />
          Vị trí: {{ placingCoords.x_percent.toFixed(1) }}%, {{ placingCoords.y_percent.toFixed(1) }}%
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showPlaceDialog = false" />
        <Button label="Đặt" icon="pi pi-map-marker" @click="submitPlaceMarker" :disabled="!placeForm.area_id" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.canvas-section {
  margin-bottom: 2rem;
  padding: 1.25rem;
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.unplaced-hint {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.coords-preview {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  background: var(--p-surface-100);
  border-radius: 6px;
}
.panel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.panel-toolbar h3 {
  margin: 0;
  font-size: 1.1rem;
}
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.form-field label {
  font-weight: 600;
  font-size: 0.875rem;
}
.file-upload-area {
  border: 2px dashed var(--p-surface-300);
  border-radius: 8px;
  padding: 1.25rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.file-upload-area:hover {
  border-color: var(--p-primary-color);
  background: color-mix(in srgb, var(--p-primary-color) 5%, transparent);
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}
.upload-placeholder i {
  font-size: 1.5rem;
}
.upload-selected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-primary-color);
  font-size: 0.85rem;
}
.upload-selected i {
  font-size: 1.1rem;
}
.file-size {
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}
.floorplan-thumb {
  width: 56px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid var(--p-surface-200);
}
.thumb-placeholder {
  width: 56px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--p-surface-100);
  border-radius: 4px;
  color: var(--p-text-muted-color);
  font-size: 1.1rem;
}
</style>
