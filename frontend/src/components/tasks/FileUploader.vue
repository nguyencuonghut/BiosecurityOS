<script setup>
/**
 * FileUploader — Presigned URL upload flow for task evidence.
 * Uses: presignUpload → XHR PUT → finalizeUpload → addTaskAttachment
 */
import { ref } from 'vue'
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
const progress = ref(0)
const uploadStage = ref('during')
const error = ref('')

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
]

const MAX_SIZES = {
  'image/jpeg': 50 * 1024 * 1024,
  'image/png': 50 * 1024 * 1024,
  'image/webp': 50 * 1024 * 1024,
  'video/mp4': 500 * 1024 * 1024,
  'video/quicktime': 500 * 1024 * 1024,
  'application/pdf': 20 * 1024 * 1024,
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 20 * 1024 * 1024,
}

function triggerFileSelect() {
  fileInput.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  error.value = ''

  // Validate type
  if (!ALLOWED_TYPES.includes(file.type)) {
    error.value = `Loại file không hỗ trợ: ${file.type}. Chấp nhận: JPEG, PNG, WebP, MP4, MOV, PDF, XLSX.`
    return
  }

  // Validate size
  const maxSize = MAX_SIZES[file.type] || 20 * 1024 * 1024
  if (file.size > maxSize) {
    error.value = `File quá lớn (${(file.size / 1024 / 1024).toFixed(1)} MB). Tối đa: ${(maxSize / 1024 / 1024).toFixed(0)} MB.`
    return
  }

  uploading.value = true
  progress.value = 0

  try {
    await store.uploadEvidence(
      props.taskId,
      file,
      uploadStage.value,
      (pct) => { progress.value = pct },
    )
    emit('uploaded')
  } catch (e) {
    error.value = e.response?.data?.error?.message || e.message || 'Upload thất bại'
  } finally {
    uploading.value = false
    // Reset file input
    if (fileInput.value) fileInput.value.value = ''
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
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
        accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,application/pdf,.xlsx"
        style="display: none"
        @change="onFileSelected"
      />
    </div>

    <ProgressBar v-if="uploading" :value="progress" class="upload-progress" />

    <div v-if="error" class="upload-error">
      <i class="pi pi-exclamation-triangle"></i> {{ error }}
    </div>

    <p class="upload-hint">
      Hỗ trợ: JPEG, PNG, WebP, MP4, MOV, PDF, XLSX.
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

.upload-error {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--p-red-50);
  color: var(--p-red-600);
  border-radius: 6px;
  font-size: 0.85rem;
}

.upload-hint {
  margin: 0.75rem 0 0;
  font-size: 0.78rem;
  color: var(--p-text-muted-color);
}
</style>
