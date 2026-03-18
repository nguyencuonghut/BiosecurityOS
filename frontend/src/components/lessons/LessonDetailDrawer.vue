<script setup>
/**
 * LessonDetailDrawer.vue — Right-side drawer showing full lesson detail.
 *
 * Props:  visible, lessonId
 * Emits:  update:visible, validated, edit, updated
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
import * as lessonService from '@/services/lessonService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  lessonId: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'validated', 'edit', 'updated'])

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

const lesson = ref(null)
const loading = ref(false)
const validating = ref(false)

// ── Reference management ─────────────────────────────────────
const showRefDialog = ref(false)
const savingRef = ref(false)
const refForm = ref({ reference_type: null, reference_id: '', contribution_note: '' })

const refTypeOptions = [
  { label: 'Scar', value: 'scar' },
  { label: 'Case', value: 'case' },
  { label: 'Task', value: 'task' },
  { label: 'Assessment', value: 'assessment' },
]

// ── Tag management ───────────────────────────────────────────
const showTagDialog = ref(false)
const savingTag = ref(false)
const tagForm = ref({ tag_type: null, tag_value: '' })

const tagTypeOptions = [
  { label: 'Loại trại', value: 'farm_type' },
  { label: 'Loại vấn đề', value: 'issue_type' },
  { label: 'Loại tuyến', value: 'route_type' },
  { label: 'Mùa vụ', value: 'season' },
  { label: 'Hình thức sở hữu', value: 'ownership_type' },
  { label: 'Hồ sơ rủi ro', value: 'risk_profile' },
  { label: 'Khác', value: 'other' },
]

watch(() => props.lessonId, async (id) => {
  if (!id) { lesson.value = null; return }
  loading.value = true
  try {
    lesson.value = await lessonService.getLesson(id)
  } catch {
    lesson.value = null
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải thông tin bài học', life: 3000 })
  } finally {
    loading.value = false
  }
}, { immediate: true })

async function onValidate() {
  if (!lesson.value) return
  validating.value = true
  try {
    lesson.value = await lessonService.validateLesson(lesson.value.id)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã xác nhận bài học', life: 3000 })
    emit('validated')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể xác nhận', life: 4000 })
  } finally {
    validating.value = false
  }
}

function onEdit() {
  emit('edit', lesson.value)
}

// ── Reference CRUD ───────────────────────────────────────────
function openRefDialog() {
  refForm.value = { reference_type: null, reference_id: '', contribution_note: '' }
  showRefDialog.value = true
}

async function onSaveRef() {
  if (!refForm.value.reference_type || !refForm.value.reference_id.trim()) return
  savingRef.value = true
  try {
    await lessonService.addReference(lesson.value.id, {
      reference_type: refForm.value.reference_type,
      reference_id: refForm.value.reference_id.trim(),
      contribution_note: refForm.value.contribution_note.trim() || null,
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm tham chiếu', life: 3000 })
    showRefDialog.value = false
    lesson.value = await lessonService.getLesson(lesson.value.id)
    emit('updated')
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.message || 'Không thể thêm tham chiếu'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 4000 })
  } finally {
    savingRef.value = false
  }
}

// ── Tag CRUD ─────────────────────────────────────────────────
function openTagDialog() {
  tagForm.value = { tag_type: null, tag_value: '' }
  showTagDialog.value = true
}

async function onSaveTag() {
  if (!tagForm.value.tag_type || !tagForm.value.tag_value.trim()) return
  savingTag.value = true
  try {
    await lessonService.addTag(lesson.value.id, {
      tag_type: tagForm.value.tag_type,
      tag_value: tagForm.value.tag_value.trim(),
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm tag', life: 3000 })
    showTagDialog.value = false
    lesson.value = await lessonService.getLesson(lesson.value.id)
    emit('updated')
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.message || 'Không thể thêm tag'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 4000 })
  } finally {
    savingTag.value = false
  }
}

function navigateToRef(ref) {
  const routeMap = {
    case: 'CaseDetail',
    task: 'TaskDetail',
  }
  const name = routeMap[ref.reference_type]
  if (name) router.push({ name, params: { id: ref.reference_id } })
}

const statusSeverity = {
  draft: 'warn',
  validated: 'success',
  archived: 'secondary',
  obsolete: 'danger',
}

const tagTypeLabels = {
  farm_type: 'Loại trại',
  issue_type: 'Loại vấn đề',
  route_type: 'Loại tuyến',
  season: 'Mùa vụ',
  ownership_type: 'Sở hữu',
  risk_profile: 'Rủi ro',
  other: 'Khác',
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
    :style="{ width: '30rem' }"
    :header="lesson ? lesson.title : 'Chi tiết Bài học'"
  >
    <div v-if="loading" class="loading-state">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
    </div>

    <div v-else-if="lesson" class="lesson-detail">
      <!-- Badge row -->
      <div class="badge-row">
        <StatusBadge :value="lesson.confidence_level" type="confidence" />
        <Tag :value="lesson.status" :severity="statusSeverity[lesson.status] || 'info'" />
        <Tag v-if="lesson.recurrence_observed" value="Tái diễn" severity="warn" />
      </div>

      <!-- Lesson number -->
      <div class="lesson-no">{{ lesson.lesson_no }}</div>

      <!-- Main sections -->
      <div class="info-sections">
        <div class="info-section">
          <h4>Bối cảnh vấn đề</h4>
          <p>{{ lesson.problem_context || '—' }}</p>
        </div>
        <div class="info-section">
          <h4>Nguyên nhân gốc</h4>
          <p>{{ lesson.root_cause_summary || '—' }}</p>
        </div>
        <div class="info-section">
          <h4>Hành động đã thực hiện</h4>
          <p>{{ lesson.action_summary || '—' }}</p>
        </div>
        <div class="info-section">
          <h4>Kết quả</h4>
          <p>{{ lesson.outcome_summary || '—' }}</p>
        </div>
        <div class="info-section" v-if="lesson.applicability_scope">
          <h4>Phạm vi áp dụng</h4>
          <p>{{ lesson.applicability_scope }}</p>
        </div>
      </div>

      <!-- Meta info -->
      <div class="info-grid">
        <div class="info-row" v-if="lesson.confirmed_at">
          <span class="info-label">Xác nhận lúc</span>
          <span class="info-value">{{ formatDateTime(lesson.confirmed_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Tạo lúc</span>
          <span class="info-value">{{ formatDateTime(lesson.created_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Cập nhật lúc</span>
          <span class="info-value">{{ formatDateTime(lesson.updated_at) }}</span>
        </div>
      </div>

      <!-- References -->
      <div class="refs-section">
        <h4>Tham chiếu</h4>
        <div v-if="lesson.references && lesson.references.length > 0">
          <div v-for="ref in lesson.references" :key="ref.id" class="ref-item">
            <Tag :value="ref.reference_type" severity="secondary" class="ref-type-tag" />
            <Button
              v-if="ref.reference_type === 'case' || ref.reference_type === 'task'"
              :label="ref.contribution_note || ref.reference_id.substring(0, 8)"
              text
              size="small"
              @click="navigateToRef(ref)"
            />
            <span v-else class="ref-text">{{ ref.contribution_note || ref.reference_id.substring(0, 8) }}</span>
          </div>
        </div>
        <p v-else class="no-refs">Chưa có tham chiếu nào.</p>
        <Button
          v-if="authStore.hasPermission('LESSON_WRITE')"
          label="Thêm tham chiếu"
          icon="pi pi-link"
          severity="secondary"
          size="small"
          outlined
          class="mt-2"
          @click="openRefDialog"
        />
      </div>

      <!-- Similarity tags -->
      <div class="tags-section">
        <h4>Similarity Tags</h4>
        <div v-if="lesson.tags && lesson.tags.length > 0" class="tags-list">
          <Tag
            v-for="tag in lesson.tags"
            :key="tag.id"
            :value="`${tagTypeLabels[tag.tag_type] || tag.tag_type}: ${tag.tag_value}`"
            severity="info"
            rounded
          />
        </div>
        <p v-else class="no-tags">Chưa có tag nào.</p>
        <Button
          v-if="authStore.hasPermission('LESSON_WRITE')"
          label="Thêm tag"
          icon="pi pi-tag"
          severity="secondary"
          size="small"
          outlined
          class="mt-2"
          @click="openTagDialog"
        />
      </div>

      <!-- Actions -->
      <div class="action-bar">
        <Button
          v-if="authStore.hasPermission('LESSON_WRITE')"
          label="Sửa"
          icon="pi pi-pencil"
          severity="info"
          outlined
          @click="onEdit"
        />
        <Button
          v-if="lesson.status === 'draft' && authStore.hasPermission('LESSON_WRITE')"
          label="Xác nhận (Validate)"
          icon="pi pi-check-circle"
          severity="success"
          :loading="validating"
          @click="onValidate"
        />
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Không tìm thấy bài học.</p>
    </div>
  </Drawer>

  <!-- ── Add Reference Dialog ──────────────────────────── -->
  <Dialog
    v-model:visible="showRefDialog"
    header="Thêm tham chiếu"
    modal
    :style="{ width: '28rem' }"
    :closable="!savingRef"
  >
    <div class="ref-form">
      <div class="form-row">
        <label>Loại đối tượng <span class="required">*</span></label>
        <Select
          v-model="refForm.reference_type"
          :options="refTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn loại"
          class="w-full"
        />
      </div>
      <div class="form-row">
        <label>ID đối tượng <span class="required">*</span></label>
        <InputText v-model="refForm.reference_id" placeholder="Nhập UUID" class="w-full" />
      </div>
      <div class="form-row">
        <label>Ghi chú đóng góp</label>
        <InputText v-model="refForm.contribution_note" placeholder="VD: Case gốc phát hiện vấn đề" class="w-full" />
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <Button label="Huỷ" severity="secondary" text @click="showRefDialog = false" :disabled="savingRef" />
        <Button label="Thêm" icon="pi pi-plus" :loading="savingRef" :disabled="!refForm.reference_type || !refForm.reference_id.trim()" @click="onSaveRef" />
      </div>
    </template>
  </Dialog>

  <!-- ── Add Tag Dialog ────────────────────────────────── -->
  <Dialog
    v-model:visible="showTagDialog"
    header="Thêm Similarity Tag"
    modal
    :style="{ width: '28rem' }"
    :closable="!savingTag"
  >
    <div class="tag-form">
      <div class="form-row">
        <label>Loại tag <span class="required">*</span></label>
        <Select
          v-model="tagForm.tag_type"
          :options="tagTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn loại"
          class="w-full"
        />
      </div>
      <div class="form-row">
        <label>Giá trị <span class="required">*</span></label>
        <InputText v-model="tagForm.tag_value" placeholder="VD: sow, vehicle_hygiene" class="w-full" />
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <Button label="Huỷ" severity="secondary" text @click="showTagDialog = false" :disabled="savingTag" />
        <Button label="Thêm" icon="pi pi-plus" :loading="savingTag" :disabled="!tagForm.tag_type || !tagForm.tag_value.trim()" @click="onSaveTag" />
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
.lesson-detail {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.badge-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.lesson-no {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  font-family: monospace;
}
.info-sections {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.info-section h4 {
  margin: 0 0 0.25rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
}
.info-section p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-line;
}
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.info-row {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
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
.refs-section h4,
.tags-section h4 {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
}
.ref-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
}
.ref-type-tag {
  min-width: 5rem;
  text-align: center;
}
.no-refs, .no-tags {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin: 0;
}
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.mt-2 { margin-top: 0.5rem; }
.action-bar {
  display: flex;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-border-color);
}
/* Dialog forms */
.ref-form,
.tag-form {
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
  font-size: 0.85rem;
  font-weight: 600;
}
.required {
  color: var(--p-red-500);
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
