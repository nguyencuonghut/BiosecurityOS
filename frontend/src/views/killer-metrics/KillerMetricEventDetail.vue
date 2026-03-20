<script setup>
/**
 * FR-08a — Killer Metric Event Detail + Evidence
 * Layout: Breadcrumb → Header (definition, severity, status tags, actions) → Tabs (Overview | Evidence)
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
import Breadcrumb from 'primevue/breadcrumb'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import Step from 'primevue/step'
import Divider from 'primevue/divider'
import ProgressBar from 'primevue/progressbar'
import { useKillerMetricStore } from '@/stores/killerMetric.js'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'
import * as attachSvc from '@/services/attachmentService.js'
import * as kmSvc from '@/services/killerMetricService.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const store = useKillerMetricStore()
const farmStore = useFarmStore()
const authStore = useAuthStore()

const activeTab = ref('0')
const event = computed(() => store.currentEvent)

// ── Breadcrumb ──
const breadcrumbItems = computed(() => [
  { label: 'Killer Metric Events', command: () => router.push('/killer-metrics/events') },
  { label: event.value?.definition?.name || '...' },
])
const breadcrumbHome = { icon: 'pi pi-bolt', command: () => router.push('/killer-metrics/events') }

// ── Status pipeline ──
const STATUS_PIPELINE = ['open', 'under_review', 'contained', 'closed']
const statusStepIndex = computed(() => {
  if (!event.value) return -1
  return STATUS_PIPELINE.indexOf(event.value.status)
})

const VALID_TRANSITIONS = {
  open: ['under_review'],
  under_review: ['contained', 'open'],
  contained: ['closed', 'under_review'],
}

function nextActions(status) {
  return VALID_TRANSITIONS[status] || []
}

// ── Status transition ──
const showTransition = ref(false)
const transitionTarget = ref(null)

function openTransition(target) {
  transitionTarget.value = target
  showTransition.value = true
}

async function confirmTransition() {
  try {
    await store.updateEvent(event.value.id, {
      status: transitionTarget.value,
      version: event.value.version,
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã chuyển sang ${statusLabel(transitionTarget.value)}`, life: 3000 })
    showTransition.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Evidence ──
const evidenceList = ref([])
const evidenceLoading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/quicktime', 'application/pdf']
const MAX_SIZE = 50 * 1024 * 1024

async function fetchEvidence() {
  if (!event.value) return
  evidenceLoading.value = true
  try {
    evidenceList.value = await kmSvc.listEventAttachments(event.value.id)
  } catch { evidenceList.value = [] }
  evidenceLoading.value = false
}

async function onPickFiles(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  for (const file of files) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.add({ severity: 'warn', summary: 'Không hỗ trợ', detail: `${file.name}: định dạng không được hỗ trợ`, life: 4000 })
      continue
    }
    if (file.size > MAX_SIZE) {
      toast.add({ severity: 'warn', summary: 'Quá lớn', detail: `${file.name}: vượt quá 50 MB`, life: 4000 })
      continue
    }
    uploading.value = true
    uploadProgress.value = 0
    try {
      const att = await attachSvc.uploadFile(file, 'killer_event', event.value.id, p => { uploadProgress.value = p })
      await kmSvc.addEventAttachment(event.value.id, { attachment_id: att.id, caption: null })
      toast.add({ severity: 'success', summary: 'Đã tải lên', detail: file.name, life: 3000 })
    } catch {
      toast.add({ severity: 'error', summary: 'Lỗi tải lên', detail: file.name, life: 5000 })
    }
  }
  uploading.value = false
  uploadProgress.value = 0
  e.target.value = ''
  await fetchEvidence()
}

async function viewFile(att) {
  try {
    const res = await attachSvc.getViewUrl(att.attachment_id)
    window.open(res.view_url, '_blank')
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể xem file', life: 4000 })
  }
}

async function downloadFile(att) {
  try {
    const res = await attachSvc.getDownloadUrl(att.attachment_id)
    const a = document.createElement('a')
    a.href = res.download_url
    a.download = att.file_name_original || 'download'
    a.click()
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải file', life: 4000 })
  }
}

async function deleteEvidence(att) {
  if (!confirm('Xóa bằng chứng này?')) return
  try {
    await kmSvc.removeEventAttachment(event.value.id, att.attachment_id)
    toast.add({ severity: 'success', summary: 'Đã xóa', life: 3000 })
    await fetchEvidence()
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể xóa', life: 5000 })
  }
}

// ── Helpers ──
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
function sourceLabel(s) {
  const m = { field_report: 'Báo cáo thực địa', camera: 'Camera giám sát', assessment: 'Đánh giá', other: 'Khác' }
  return m[s] || s
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function fileIcon(mime) {
  if (!mime) return 'pi pi-file'
  if (mime.startsWith('image/')) return 'pi pi-image'
  if (mime.startsWith('video/')) return 'pi pi-video'
  if (mime === 'application/pdf') return 'pi pi-file-pdf'
  return 'pi pi-file'
}
function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
function farmName(farmId) {
  return farmStore.farms.find(f => f.id === farmId)?.name || farmId?.slice(0, 8)
}

const EDITABLE_STATUSES = ['open', 'under_review']
const canUploadEvidence = computed(() => {
  return event.value && EDITABLE_STATUSES.includes(event.value.status)
    && authStore.hasPermission('KILLER_EVENT_WRITE')
    && authStore.hasPermission('ATTACHMENT_UPLOAD')
})
const canDeleteEvidence = computed(() => {
  return event.value && EDITABLE_STATUSES.includes(event.value.status)
    && authStore.hasPermission('KILLER_EVENT_WRITE')
    && authStore.hasPermission('ATTACHMENT_DELETE')
})

// ── Init ──
onMounted(async () => {
  const id = route.params.id
  await Promise.all([
    store.fetchEvent(id),
    farmStore.fetchFarms(),
    store.fetchDefinitions(),
  ])
  await fetchEvidence()
})
</script>

<template>
  <Toast />
  <div class="event-detail-page" v-if="event">
    <!-- Breadcrumb -->
    <Breadcrumb :model="breadcrumbItems" :home="breadcrumbHome" class="event-breadcrumb" />

    <!-- Header -->
    <div class="event-header">
      <div class="header-top">
        <div class="header-title-block">
          <h1 class="event-title">
            <i class="pi pi-bolt" style="color: var(--p-red-500)"></i>
            {{ event.definition?.name || 'Killer Metric Event' }}
          </h1>
          <div class="header-tags">
            <Tag :value="event.definition?.severity_level" :severity="severityColor(event.definition?.severity_level)" />
            <Tag :value="statusLabel(event.status)" :severity="statusColor(event.status)" />
            <Tag :value="event.definition?.code" severity="secondary" v-if="event.definition?.code" />
          </div>
        </div>
        <div class="header-actions" v-if="authStore.hasPermission('KILLER_EVENT_WRITE') && event.status !== 'closed'">
          <Button
            v-for="target in nextActions(event.status)"
            :key="target"
            :label="statusLabel(target)"
            size="small"
            :severity="statusColor(target)"
            outlined
            @click="openTransition(target)"
          />
        </div>
      </div>

      <!-- Status Pipeline -->
      <div class="pipeline-wrap">
        <Stepper :value="statusStepIndex" linear class="event-stepper">
          <StepList>
            <Step v-for="(step, idx) in STATUS_PIPELINE" :key="step" :value="idx">
              {{ statusLabel(step) }}
            </Step>
          </StepList>
        </Stepper>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab" class="event-tabs">
      <TabList>
        <Tab value="0">Tổng quan</Tab>
        <Tab value="1">Bằng chứng ({{ evidenceList.length }})</Tab>
      </TabList>
      <TabPanels>
        <!-- Tab 0: Overview -->
        <TabPanel value="0">
          <div class="overview-grid">
            <div class="overview-left">
              <div class="info-card">
                <h3>Chi tiết sự kiện</h3>
                <div class="info-row">
                  <label>Mô tả</label>
                  <p>{{ event.summary }}</p>
                </div>
                <Divider />
                <div class="info-meta">
                  <div class="meta-item">
                    <label>Trại</label>
                    <span>{{ farmName(event.farm_id) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Nguồn</label>
                    <span>{{ sourceLabel(event.source_type) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Thời gian sự kiện</label>
                    <span>{{ formatDate(event.event_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Ngày tạo</label>
                    <span>{{ formatDate(event.created_at) }}</span>
                  </div>
                  <div class="meta-item" v-if="event.resolved_at">
                    <label>Ngày xử lý xong</label>
                    <span>{{ formatDate(event.resolved_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Version</label>
                    <span>{{ event.version }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="overview-right">
              <div class="info-card">
                <h3>Phân loại vi phạm</h3>
                <div class="info-row">
                  <label>Loại</label>
                  <p>{{ event.definition?.name || '—' }}</p>
                </div>
                <div class="info-row">
                  <label>Mã</label>
                  <p>{{ event.definition?.code || '—' }}</p>
                </div>
                <div class="info-row">
                  <label>Mức nghiêm trọng</label>
                  <Tag :value="event.definition?.severity_level" :severity="severityColor(event.definition?.severity_level)" />
                </div>
              </div>

              <div class="info-card">
                <h3>Bằng chứng</h3>
                <div class="evidence-summary">
                  <i class="pi pi-paperclip"></i>
                  <span>{{ evidenceList.length }} file đính kèm</span>
                </div>
                <Button
                  label="Xem bằng chứng"
                  icon="pi pi-images"
                  size="small"
                  severity="info"
                  outlined
                  class="mt-half"
                  @click="activeTab = '1'"
                />
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- Tab 1: Evidence -->
        <TabPanel value="1">
          <div class="evidence-section">
            <div class="section-header">
              <h3>Bằng chứng / Minh chứng</h3>
            </div>

            <!-- Upload area -->
            <div v-if="canUploadEvidence" class="upload-area">
              <label class="upload-label">
                <i class="pi pi-cloud-upload"></i>
                <span>Chọn file (ảnh, video, PDF — tối đa 50 MB)</span>
                <input type="file" multiple accept="image/*,video/mp4,video/quicktime,application/pdf" @change="onPickFiles" class="hidden-input" />
              </label>
              <ProgressBar v-if="uploading" :value="uploadProgress" :showValue="true" class="upload-progress" />
            </div>

            <!-- File list -->
            <div v-if="evidenceLoading" class="evidence-loading">
              <i class="pi pi-spin pi-spinner"></i> Đang tải...
            </div>
            <div v-else-if="evidenceList.length === 0" class="evidence-empty">
              Chưa có bằng chứng nào được đính kèm.
            </div>
            <div v-else class="evidence-list">
              <div v-for="att in evidenceList" :key="att.id" class="evidence-item">
                <div class="ev-info">
                  <i :class="fileIcon(att.mime_type)" class="ev-icon"></i>
                  <div>
                    <div class="ev-name">{{ att.file_name_original || 'file' }}</div>
                    <div class="ev-meta">{{ formatSize(att.file_size_bytes) }} · {{ formatDate(att.uploaded_at) }}</div>
                  </div>
                </div>
                <div class="ev-actions">
                  <Button icon="pi pi-eye" size="small" severity="info" text v-tooltip.top="'Xem'" @click="viewFile(att)" />
                  <Button icon="pi pi-download" size="small" severity="secondary" text v-tooltip.top="'Tải'" @click="downloadFile(att)" />
                  <Button
                      v-if="canDeleteEvidence"
                    icon="pi pi-trash" size="small" severity="danger" text v-tooltip.top="'Xóa'"
                    @click="deleteEvidence(att)"
                  />
                </div>
              </div>
            </div>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>

  <!-- Loading -->
  <div v-else class="loading-state">
    <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
    <p>Đang tải sự kiện...</p>
  </div>

  <!-- Transition Dialog -->
  <Dialog v-model:visible="showTransition" header="Xác nhận chuyển trạng thái" modal :style="{ width: '420px' }">
    <p v-if="event">
      Chuyển sự kiện <strong>{{ event.definition?.name }}</strong>
      từ <Tag :value="statusLabel(event.status)" :severity="statusColor(event.status)" />
      sang <Tag :value="statusLabel(transitionTarget)" :severity="statusColor(transitionTarget)" /> ?
    </p>
    <template #footer>
      <Button label="Hủy" severity="secondary" text @click="showTransition = false" />
      <Button label="Xác nhận" icon="pi pi-check" @click="confirmTransition" />
    </template>
  </Dialog>
</template>

<style scoped>
.event-detail-page { width: 100%; }
.event-breadcrumb { margin-bottom: 1rem; }

/* Header */
.event-header {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;
}
.header-top { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; }
.header-title-block { flex: 1; min-width: 0; }
.event-title {
  margin: 0 0 0.5rem; font-size: 1.25rem;
  display: flex; align-items: center; gap: 0.5rem;
}
.header-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.pipeline-wrap { margin-top: 1.25rem; }

/* Tabs */
.event-tabs { margin-top: 0; }

/* Overview */
.overview-grid { display: grid; grid-template-columns: 1fr 340px; gap: 1.5rem; }
.info-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem;
}
.info-card h3 { margin: 0 0 1rem; font-size: 1rem; }
.info-row { margin-bottom: 1rem; }
.info-row label { display: block; font-size: 0.75rem; color: var(--p-text-muted-color); font-weight: 600; margin-bottom: 0.25rem; }
.info-row p { margin: 0; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }
.info-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.meta-item label { display: block; font-size: 0.75rem; color: var(--p-text-muted-color); font-weight: 600; margin-bottom: 0.15rem; }
.meta-item span { font-size: 0.85rem; }

.evidence-summary {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.9rem; color: var(--p-text-muted-color);
}
.mt-half { margin-top: 0.75rem; }

/* Evidence */
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-header h3 { margin: 0; }

.upload-area { margin-bottom: 1rem; }
.upload-label {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: 2px dashed var(--p-surface-300);
  border-radius: 8px; cursor: pointer;
  color: var(--p-text-muted-color); font-size: 0.85rem;
  transition: border-color 0.2s;
}
.upload-label:hover { border-color: var(--p-primary-color); color: var(--p-primary-color); }
.hidden-input { display: none; }
.upload-progress { margin-top: 0.5rem; height: 6px; }

.evidence-loading, .evidence-empty {
  text-align: center; padding: 2rem;
  color: var(--p-text-muted-color); font-size: 0.85rem;
}
.evidence-list { display: flex; flex-direction: column; gap: 0.5rem; }
.evidence-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--p-surface-50); border-radius: 6px; gap: 0.5rem;
}
.ev-info { display: flex; align-items: center; gap: 0.5rem; min-width: 0; flex: 1; }
.ev-icon { font-size: 1.2rem; color: var(--p-primary-color); flex-shrink: 0; }
.ev-name { font-size: 0.85rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ev-meta { font-size: 0.75rem; color: var(--p-text-muted-color); }
.ev-actions { display: flex; gap: 0.15rem; flex-shrink: 0; }

/* Utility */
.muted { color: var(--p-text-muted-color); font-size: 0.85rem; }
.loading-state { text-align: center; padding: 3rem; color: var(--p-text-muted-color); }

@media (max-width: 768px) {
  .overview-grid { grid-template-columns: 1fr; }
  .header-top { flex-direction: column; }
}
</style>
