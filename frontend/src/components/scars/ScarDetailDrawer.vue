<script setup>
/**
 * ScarDetailDrawer.vue — Right-side drawer showing full scar detail.
 *
 * Props:
 *   visible  — v-model:visible
 *   scarId   — UUID of the scar to load
 *   farmId   — UUID of the farm (for navigation)
 *
 * Emits:
 *   update:visible
 *   validated — when scar is validated
 */

import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Drawer from 'primevue/drawer'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth.js'
import * as scarService from '@/services/scarService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  scarId: { type: String, default: null },
  farmId: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'validated', 'edit', 'updated'])

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

const scar = ref(null)
const loading = ref(false)
const validating = ref(false)

// ── Link management ──────────────────────────────────────────
const showLinkDialog = ref(false)
const savingLink = ref(false)
const linkForm = ref({ linked_object_type: null, linked_object_id: '', link_reason: '' })

const linkTypeOptions = [
  { label: 'Case', value: 'case' },
  { label: 'Task', value: 'task' },
  { label: 'Assessment', value: 'assessment' },
  { label: 'Attachment', value: 'attachment' },
]

watch(() => props.scarId, async (id) => {
  if (!id) { scar.value = null; return }
  loading.value = true
  try {
    scar.value = await scarService.getScar(id)
  } catch {
    scar.value = null
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải thông tin scar', life: 3000 })
  } finally {
    loading.value = false
  }
}, { immediate: true })

async function onValidate() {
  if (!scar.value) return
  validating.value = true
  try {
    scar.value = await scarService.validateScar(scar.value.id)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã xác nhận scar', life: 3000 })
    emit('validated')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể xác nhận', life: 4000 })
  } finally {
    validating.value = false
  }
}

function navigateToCase(caseId) {
  router.push({ name: 'CaseDetail', params: { id: caseId } })
}

function navigateToTask(taskId) {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

function onEdit() {
  emit('edit', scar.value)
}

function openLinkDialog() {
  linkForm.value = { linked_object_type: null, linked_object_id: '', link_reason: '' }
  showLinkDialog.value = true
}

async function onSaveLink() {
  if (!linkForm.value.linked_object_type || !linkForm.value.linked_object_id.trim()) return
  savingLink.value = true
  try {
    await scarService.addScarLink(scar.value.id, {
      linked_object_type: linkForm.value.linked_object_type,
      linked_object_id: linkForm.value.linked_object_id.trim(),
      link_reason: linkForm.value.link_reason.trim() || null,
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm liên kết', life: 3000 })
    showLinkDialog.value = false
    // Reload scar to show new link
    scar.value = await scarService.getScar(scar.value.id)
    emit('updated')
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.message || 'Không thể thêm liên kết'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 4000 })
  } finally {
    savingLink.value = false
  }
}

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

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('vi-VN')
}

function formatDateTime(val) {
  if (!val) return '—'
  return new Date(val).toLocaleString('vi-VN')
}
</script>

<template>
  <Drawer
    :visible="props.visible"
    @update:visible="emit('update:visible', $event)"
    position="right"
    :style="{ width: '28rem' }"
    :header="scar ? scar.title : 'Chi tiết Scar'"
  >
    <div v-if="loading" class="loading-state">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
    </div>

    <div v-else-if="scar" class="scar-detail">
      <!-- Type + Confidence badges -->
      <div class="badge-row">
        <Tag :value="scarTypeLabels[scar.scar_type] || scar.scar_type" :severity="scarTypeSeverity[scar.scar_type] || 'info'" />
        <StatusBadge :value="scar.confidence_level" type="confidence" />
        <Tag v-if="scar.recurrence_flag" value="Lặp lại" severity="warn" />
      </div>

      <!-- Main info -->
      <div class="info-grid">
        <div class="info-row">
          <span class="info-label">Mô tả</span>
          <span class="info-value">{{ scar.description || '—' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Nguồn rủi ro</span>
          <span class="info-value">{{ scar.source_of_risk || '—' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Ngày sự kiện</span>
          <span class="info-value">{{ formatDate(scar.event_date) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Trạng thái</span>
          <Tag :value="scar.status" :severity="scar.status === 'active' ? 'success' : 'secondary'" />
        </div>
        <div class="info-row">
          <span class="info-label">Vị trí</span>
          <span class="info-value">
            {{ scar.x_percent != null ? `(${scar.x_percent}%, ${scar.y_percent}%)` : 'Không xác định' }}
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">Số lần lặp lại</span>
          <span class="info-value">{{ scar.recurrence_count }}</span>
        </div>
        <div class="info-row" v-if="scar.validated_at">
          <span class="info-label">Xác nhận lúc</span>
          <span class="info-value">{{ formatDateTime(scar.validated_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Tạo lúc</span>
          <span class="info-value">{{ formatDateTime(scar.created_at) }}</span>
        </div>
      </div>

      <!-- Linked objects -->
      <div class="links-section" v-if="scar.links && scar.links.length > 0">
        <h4>Liên kết</h4>
        <div v-for="link in scar.links" :key="link.id" class="link-item">
          <Tag :value="link.linked_object_type" severity="secondary" class="link-type-tag" />
          <Button
            v-if="link.linked_object_type === 'case'"
            :label="link.link_reason || link.linked_object_id.substring(0, 8)"
            text
            size="small"
            @click="navigateToCase(link.linked_object_id)"
          />
          <Button
            v-else-if="link.linked_object_type === 'task'"
            :label="link.link_reason || link.linked_object_id.substring(0, 8)"
            text
            size="small"
            @click="navigateToTask(link.linked_object_id)"
          />
          <span v-else class="link-text">{{ link.link_reason || link.linked_object_id.substring(0, 8) }}</span>
        </div>
      </div>
      <div v-else class="links-section">
        <h4>Liên kết</h4>
        <p class="no-links">Chưa có liên kết nào.</p>
      </div>

      <!-- Add link button -->
      <div v-if="authStore.hasPermission('SCAR_WRITE')" class="add-link-bar">
        <Button label="Thêm liên kết" icon="pi pi-link" severity="secondary" size="small" outlined @click="openLinkDialog" />
      </div>

      <!-- Actions -->
      <div class="action-bar">
        <Button
          v-if="authStore.hasPermission('SCAR_WRITE')"
          label="Sửa"
          icon="pi pi-pencil"
          severity="info"
          outlined
          @click="onEdit"
        />
        <Button
          v-if="scar.confidence_level !== 'confirmed' && authStore.hasPermission('SCAR_WRITE')"
          label="Xác nhận (Validate)"
          icon="pi pi-check-circle"
          severity="success"
          :loading="validating"
          @click="onValidate"
        />
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Không tìm thấy scar.</p>
    </div>
  </Drawer>

  <!-- ── Add Link Dialog ──────────────────────────────────── -->
  <Dialog
    v-model:visible="showLinkDialog"
    header="Thêm liên kết"
    modal
    :style="{ width: '28rem' }"
    :closable="!savingLink"
  >
    <div class="link-form">
      <div class="form-row">
        <label>Loại đối tượng <span class="required">*</span></label>
        <Select
          v-model="linkForm.linked_object_type"
          :options="linkTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn loại"
          class="w-full"
        />
      </div>
      <div class="form-row">
        <label>ID đối tượng <span class="required">*</span></label>
        <InputText v-model="linkForm.linked_object_id" placeholder="Nhập UUID" class="w-full" />
      </div>
      <div class="form-row">
        <label>Lý do</label>
        <InputText v-model="linkForm.link_reason" placeholder="VD: Liên quan đến case XYZ" class="w-full" />
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <Button label="Huỷ" severity="secondary" text @click="showLinkDialog = false" :disabled="savingLink" />
        <Button label="Thêm" icon="pi pi-plus" :loading="savingLink" :disabled="!linkForm.linked_object_type || !linkForm.linked_object_id.trim()" @click="onSaveLink" />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--p-text-muted-color);
}
.scar-detail {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.badge-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.info-row {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
}
.info-value {
  font-size: 0.9rem;
}
.links-section h4 {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
}
.link-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
}
.link-type-tag {
  font-size: 0.7rem;
  min-width: 70px;
  text-align: center;
}
.link-text {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.no-links {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin: 0;
}
.add-link-bar {
  padding-top: 0.25rem;
}
.action-bar {
  display: flex;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-surface-200);
}
.link-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.form-row label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}
.required {
  color: var(--p-red-500);
}
.w-full {
  width: 100%;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
