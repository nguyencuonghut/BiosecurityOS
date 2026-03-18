<script setup>
/**
 * EvidenceGallery — Display task attachments as a grid with thumbnails/icons.
 * Supports image preview, download link for other file types.
 */
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import * as attachSvc from '@/services/attachmentService.js'

const props = defineProps({
  taskAttachments: { type: Array, default: () => [] },
})

const previewVisible = ref(false)
const previewUrl = ref('')
const previewName = ref('')
const loadingId = ref(null)

// Group by upload_stage
const grouped = computed(() => {
  const groups = { before: [], during: [], after: [], review: [] }
  for (const ta of props.taskAttachments) {
    const stage = ta.upload_stage || 'during'
    if (groups[stage]) groups[stage].push(ta)
    else groups.during.push(ta)
  }
  return groups
})

const stageLabels = { before: 'Trước xử lý', during: 'Trong quá trình', after: 'Sau xử lý', review: 'Review' }

function isImage(mimeType) {
  return mimeType?.startsWith('image/')
}

function isVideo(mimeType) {
  return mimeType?.startsWith('video/')
}

function fileIcon(mimeType) {
  if (isImage(mimeType)) return 'pi pi-image'
  if (isVideo(mimeType)) return 'pi pi-video'
  if (mimeType === 'application/pdf') return 'pi pi-file-pdf'
  return 'pi pi-file'
}

function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const BROWSER_VIEWABLE = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'video/mp4', 'video/quicktime', 'application/pdf']

function canViewInBrowser(mimeType) {
  return BROWSER_VIEWABLE.includes(mimeType)
}

async function openPreview(ta) {
  loadingId.value = ta.attachment_id
  try {
    if (canViewInBrowser(ta.mime_type)) {
      // Get view URL (inline disposition) and open in new tab
      const result = await attachSvc.getViewUrl(ta.attachment_id)
      window.open(result.view_url, '_blank', 'noopener')
    } else {
      const result = await attachSvc.getDownloadUrl(ta.attachment_id)
      previewUrl.value = result.download_url
      previewName.value = ta.file_name_original || 'file'
      previewVisible.value = true
    }
  } catch {
    window.open(`/api/v1/attachments/${ta.attachment_id}/download`, '_blank')
  } finally {
    loadingId.value = null
  }
}

async function downloadFile(ta) {
  loadingId.value = ta.attachment_id
  try {
    const result = await attachSvc.getDownloadUrl(ta.attachment_id)
    const a = document.createElement('a')
    a.href = result.download_url
    a.download = ta.file_name_original || 'download'
    a.target = '_blank'
    a.click()
  } catch {
    // fallback
  } finally {
    loadingId.value = null
  }
}
</script>

<template>
  <div class="evidence-gallery">
    <template v-for="(items, stage) in grouped" :key="stage">
      <div v-if="items.length" class="stage-group">
        <h4 class="stage-label">{{ stageLabels[stage] }} ({{ items.length }})</h4>
        <div class="gallery-grid">
          <div v-for="ta in items" :key="ta.id" class="evidence-card" @click="openPreview(ta)">
            <div class="thumb-area">
              <i :class="fileIcon(ta.mime_type)" class="file-type-icon"></i>
              <Tag v-if="ta.is_primary_evidence" value="Primary" severity="success" class="primary-badge" />
            </div>
            <div class="card-info">
              <span class="file-name" :title="ta.file_name_original">{{ ta.file_name_original || 'Attachment' }}</span>
              <span class="file-meta">{{ formatSize(ta.file_size_bytes) }}</span>
            </div>
            <div class="card-actions">
              <Button
                v-if="canViewInBrowser(ta.mime_type)"
                icon="pi pi-external-link"
                size="small"
                text
                rounded
                title="Mở trong tab mới"
                :loading="loadingId === ta.attachment_id"
                @click.stop="openPreview(ta)"
              />
              <Button
                icon="pi pi-download"
                size="small"
                text
                rounded
                title="Tải xuống"
                :loading="loadingId === ta.attachment_id"
                @click.stop="downloadFile(ta)"
              />
            </div>
          </div>
        </div>
      </div>
    </template>

    <p v-if="!taskAttachments?.length" class="empty-msg">Chưa có bằng chứng nào được tải lên.</p>

    <!-- Preview Dialog -->
    <Dialog v-model:visible="previewVisible" :header="previewName" modal :style="{ width: '80vw', maxWidth: '900px' }">
      <div class="preview-content">
        <img v-if="previewUrl && previewName.match(/\.(jpg|jpeg|png|webp)$/i)" :src="previewUrl" :alt="previewName" class="preview-image" />
        <video v-else-if="previewUrl && previewName.match(/\.(mp4|mov)$/i)" :src="previewUrl" controls class="preview-video" />
        <div v-else class="preview-fallback">
          <i class="pi pi-file" style="font-size: 3rem; color: var(--p-text-muted-color)"></i>
          <p>Không thể xem trước file này.</p>
          <a :href="previewUrl" target="_blank" class="download-link">Tải xuống</a>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.evidence-gallery { }

.stage-group { margin-bottom: 1.5rem; }
.stage-label {
  font-size: 0.85rem; font-weight: 600;
  color: var(--p-text-muted-color);
  margin: 0 0 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.evidence-card {
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.evidence-card:hover {
  border-color: var(--p-primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.thumb-area {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  background: var(--p-surface-ground);
  border-radius: 6px;
}

.file-type-icon { font-size: 1.5rem; color: var(--p-text-muted-color); }
.primary-badge { position: absolute; top: 4px; right: 4px; font-size: 0.7rem; }

.card-info { display: flex; flex-direction: column; }
.file-name {
  font-size: 0.82rem; font-weight: 600;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.file-meta { font-size: 0.75rem; color: var(--p-text-muted-color); }

.card-actions { display: flex; justify-content: flex-end; }

.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); font-size: 0.85rem; }

/* Preview */
.preview-content { text-align: center; }
.preview-image { max-width: 100%; max-height: 70vh; border-radius: 4px; }
.preview-video { max-width: 100%; max-height: 70vh; border-radius: 4px; }
.preview-fallback { padding: 2rem; }
.download-link { color: var(--p-primary-color); text-decoration: underline; font-weight: 600; }
</style>
