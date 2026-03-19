<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import { useAuthStore } from '@/stores/auth.js'
import * as floorplanService from '@/services/floorplanService.js'
import * as attachmentService from '@/services/attachmentService.js'

const props = defineProps({
  farmId: { type: String, required: true },
})

const toast = useToast()
const authStore = useAuthStore()

const floorplans = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const uploadProgress = ref(0)
const selectedFile = ref(null)
const fileInputRef = ref(null)
// Preview images keyed by floorplan id
const previewUrls = ref({})

const ALLOWED_MIME = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
const MAX_SIZE = 50 * 1024 * 1024 // 50MB

const form = ref({
  title: '',
  effective_from: null,
})

onMounted(() => fetchFloorplans())

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
</script>

<template>
  <div class="floorplan-panel">
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
  </div>
</template>

<style scoped>
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
