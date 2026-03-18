<script setup>
/**
 * LessonFormDialog.vue — Create / Edit lesson dialog.
 *
 * Props:  visible, lesson (null = create, object = edit)
 * Emits:  update:visible, saved
 */

import { ref, computed, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import * as lessonService from '@/services/lessonService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  lesson: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()
const saving = ref(false)

const isEdit = computed(() => !!props.lesson)
const dialogTitle = computed(() => isEdit.value ? 'Sửa Bài học' : 'Tạo Bài học mới')

// ── Form fields ───────────────────────────────────────────────
const form = ref(emptyForm())

function emptyForm() {
  return {
    title: '',
    problem_context: '',
    root_cause_summary: '',
    action_summary: '',
    outcome_summary: '',
    recurrence_observed: false,
    applicability_scope: '',
    confidence_level: null,
  }
}

const confidenceOptions = [
  { label: 'Nghi ngờ', value: 'suspected' },
  { label: 'Có thể', value: 'probable' },
  { label: 'Xác nhận', value: 'confirmed' },
]

watch(() => props.visible, (val) => {
  if (!val) return
  if (isEdit.value) {
    form.value = {
      title: props.lesson.title,
      problem_context: props.lesson.problem_context || '',
      root_cause_summary: props.lesson.root_cause_summary || '',
      action_summary: props.lesson.action_summary || '',
      outcome_summary: props.lesson.outcome_summary || '',
      recurrence_observed: props.lesson.recurrence_observed || false,
      applicability_scope: props.lesson.applicability_scope || '',
      confidence_level: props.lesson.confidence_level,
    }
  } else {
    form.value = emptyForm()
  }
})

// ── Validation ────────────────────────────────────────────────
const formValid = computed(() => {
  return form.value.title.trim() && form.value.problem_context.trim() && form.value.confidence_level
})

// ── Save ──────────────────────────────────────────────────────
async function onSave() {
  if (!formValid.value) return
  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      problem_context: form.value.problem_context.trim(),
      root_cause_summary: form.value.root_cause_summary.trim() || null,
      action_summary: form.value.action_summary.trim() || null,
      outcome_summary: form.value.outcome_summary.trim() || null,
      recurrence_observed: form.value.recurrence_observed,
      applicability_scope: form.value.applicability_scope.trim() || null,
      confidence_level: form.value.confidence_level,
    }

    if (isEdit.value) {
      await lessonService.updateLesson(props.lesson.id, payload)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã cập nhật bài học', life: 3000 })
    } else {
      await lessonService.createLesson(payload)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo bài học mới', life: 3000 })
    }

    emit('update:visible', false)
    emit('saved')
  } catch (err) {
    const msg = err.response?.data?.message || err.response?.data?.error?.message || 'Không thể lưu'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 4000 })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    @update:visible="emit('update:visible', $event)"
    :header="dialogTitle"
    modal
    :style="{ width: '36rem' }"
    :closable="!saving"
  >
    <div class="lesson-form">
      <div class="form-row">
        <label>Tiêu đề <span class="required">*</span></label>
        <InputText v-model="form.title" placeholder="Tiêu đề bài học" class="w-full" />
      </div>

      <div class="form-row">
        <label>Bối cảnh vấn đề <span class="required">*</span></label>
        <Textarea v-model="form.problem_context" rows="3" autoResize placeholder="Mô tả bối cảnh vấn đề..." class="w-full" />
      </div>

      <div class="form-row">
        <label>Nguyên nhân gốc</label>
        <Textarea v-model="form.root_cause_summary" rows="2" autoResize placeholder="Phân tích nguyên nhân gốc..." class="w-full" />
      </div>

      <div class="form-row">
        <label>Hành động đã thực hiện</label>
        <Textarea v-model="form.action_summary" rows="2" autoResize placeholder="Hành động khắc phục..." class="w-full" />
      </div>

      <div class="form-row">
        <label>Kết quả</label>
        <Textarea v-model="form.outcome_summary" rows="2" autoResize placeholder="Kết quả sau hành động..." class="w-full" />
      </div>

      <div class="form-row">
        <label>Độ tin cậy <span class="required">*</span></label>
        <Select
          v-model="form.confidence_level"
          :options="confidenceOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn mức độ tin cậy"
          class="w-full"
        />
      </div>

      <div class="form-row">
        <label>Phạm vi áp dụng</label>
        <InputText v-model="form.applicability_scope" placeholder="VD: Tất cả trại nái miền Nam" class="w-full" />
      </div>

      <div class="form-row-inline">
        <Checkbox v-model="form.recurrence_observed" :binary="true" inputId="recurrence" />
        <label for="recurrence">Đã tái diễn</label>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <Button label="Huỷ" severity="secondary" text @click="emit('update:visible', false)" :disabled="saving" />
        <Button :label="isEdit ? 'Cập nhật' : 'Tạo mới'" icon="pi pi-check" :loading="saving" :disabled="!formValid" @click="onSave" />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.lesson-form {
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
.form-row-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.form-row-inline label {
  font-size: 0.9rem;
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
