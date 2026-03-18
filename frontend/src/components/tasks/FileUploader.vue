<script setup>
/**
 * FileUploader — Presigned URL upload flow for task evidence.
 * Supports multiple file selection & sequential upload.
 * Uses: presignUpload → XHR PUT → finalizeUpload → addTaskAttachment
 */
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import Select from 'primevue/select'
import { useTaskStore } from '@/stores/task.js'

const props = defineProps({
  taskId: { type: String, required: true },
})

const emit = defineEmits(['uploaded'])

const store = useTaskStore()
const fileInput = ref(null)
const uploading = ref(false)
const uploadStage = ref('during')

// Each entry: { name, size, progress, status: 'pending'|'uploading'|'done'|'error', error? }
const fileQueue = ref([])

const stageOptions = [
  { label: 'Trước (before)', value: 'before' },
  { label: 'Trong quá trình (during)', value: 'during' },
  { label: 'Sau (after)', value: 'after' },
  { label: 'Review', value: 'review' },
]

const ALLOWED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp',
  'video/mp4', 'video/quicktime',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/wps-office.xlsx',
]

const MAX_SIZES = {
  'image/jpeg': 50 * 1024 * 1024,
  'image/png': 50 * 1024 * 1024,
  'image/webp': 50 * 1024 * 1024,
  'video/mp4': 500 * 1024 * 1024,
  'video/quicktime': 500 * 1024 * 1024,
  'application/pdf': 20 * 1024 * 1024,
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 20 * 1024 * 1024,
  'application/wps-office.xlsx': 20 * 1024 * 1024,
}

const overallProgress = computed(() => {
  if (!fileQueue.value.length) return 0
  const sum = fileQueue.value.reduce((acc, f) => acc + f.progress, 0)
  return Math.round(sum / fileQueue.value.length)
})

function triggerFileSelect() {
  fileInput.value?.click()
}

function validateFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return `Loại file không hỗ trợ: ${file.type}`
  }
  const maxSize = MAX_SIZES[file.type] || 20 * 1024 * 1024
  if (file.size > maxSize) {
    return `File quá lớn (${formatSize(file.size)}). Tối đa: ${formatSize(maxSize)}`
  }
  return null
}

async function onFileSelected(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  // Build queue with validation
  const queue = files.map((file) => {
    const validationError = validateFile(file)
    return {
      file,
      name: file.name,
      size: file.size,
      progress: validationError ? 0 : 0,
      status: validationError ? 'error' : 'pending',
      error: validationError || '',
    }
  })
  fileQueue.value = queue

  const validFiles = queue.filter((f) => f.status === 'pending')
  if (!validFiles.length) return

  uploading.value = true
  let anySuccess = false

  // Upload sequentially
  for (const entry of validFiles) {
    entry.status = 'uploading'
    try {
      await store.uploadEvidence(
        props.taskId,
        entry.file,
        uploadStage.value,
        (pct) => { entry.progress = pct },
      )
      entry.progress = 100
      entry.status = 'done'
      anySuccess = true
    } catch (e) {
      entry.status = 'error'
      entry.error = e.response?.data?.error?.message || e.message || 'Upload thất bại'
    }
  }

  uploading.value = false
  if (fileInput.value) fileInput.value.value = ''
  if (anySuccess) emit('uploaded')
}

function clearQueue() {
  fileQueue.value = []
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function statusIcon(status) {
  switch (status) {
    case 'done': return 'pi pi-check-circle'
    case 'error': return 'pi pi-exclamation-triangle'
    case 'uploading': return 'pi pi-spin pi-spinner'
    default: return 'pi pi-clock'
  }
}
</script>

<template>
  <div class="file-uploader">
    <div class="upload-controls">
      <Select
        v-model="uploadStage"
        :options="stageOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Giai đoạn"
        class="stage-select"
        :disabled="uploading"
      />
      <Button
        label="Chọn file"
        icon="pi pi-upload"
        :loading="uploading"
        @click="triggerFileSelect"
        size="small"
      />
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,application/pdf,.xlsx"
        style="display: none"
        @change="onFileSelected"
      />
    </div>

    <!-- Overall progress -->
    <ProgressBar v-if="uploading" :value="overallProgress" class="upload-progress" />

    <!-- Per-file status list -->
    <ul v-if="fileQueue.length" class="file-queue">
      <li v-for="(entry, idx) in fileQueue" :key="idx" class="file-queue-item" :class="entry.status">
        <div class="file-info">
          <i :class="statusIcon(entry.status)"></i>
          <span class="file-name">{{ entry.name }}</span>
          <span class="file-size">{{ formatSize(entry.size) }}</span>
        </div>
        <ProgressBar v-if="entry.status === 'uploading'" :value="entry.progress" class="file-progress" />
        <div v-if="entry.error" class="file-error">{{ entry.error }}</div>
      </li>
    </ul>

    <div v-if="fileQueue.length && !uploading" class="queue-actions">
      <Button label="Xóa danh sách" icon="pi pi-times" severity="secondary" text size="small" @click="clearQueue" />
    </div>

    <p class="upload-hint">
      Hỗ trợ: JPEG, PNG, WebP, MP4, MOV, PDF, XLSX — chọn nhiều file cùng lúc.
      Tối đa: Ảnh 50MB, Video 500MB, Tài liệu 20MB.
    </p>
  </div>
</template>

<style scoped>
.file-uploader {
  background: var(--p-surface-ground);
  border: 2px dashed var(--p-surface-border);
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.upload-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.stage-select { min-width: 180px; }

.upload-progress { margin-top: 0.75rem; }

.file-queue {
  list-style: none;
  padding: 0;
  margin: 0.75rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-queue-item {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
}

.file-queue-item.done {
  border-color: var(--p-green-300);
  background: var(--p-green-50);
}

.file-queue-item.error {
  border-color: var(--p-red-300);
  background: var(--p-red-50);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.file-info .pi-check-circle { color: var(--p-green-600); }
.file-info .pi-exclamation-triangle { color: var(--p-red-600); }
.file-info .pi-spinner { color: var(--p-primary-color); }
.file-info .pi-clock { color: var(--p-text-muted-color); }

.file-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.file-size {
  color: var(--p-text-muted-color);
  font-size: 0.78rem;
  margin-left: auto;
}

.file-progress { margin-top: 0.4rem; }

.file-error {
  margin-top: 0.25rem;
  font-size: 0.78rem;
  color: var(--p-red-600);
}

.queue-actions { margin-top: 0.5rem; }

.upload-hint {
  margin: 0.75rem 0 0;
  font-size: 0.78rem;
  color: var(--p-text-muted-color);
}
</style>
