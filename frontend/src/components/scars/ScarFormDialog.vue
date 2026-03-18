<script setup>
/**
 * ScarFormDialog.vue — Create / Edit scar dialog.
 *
 * Props:
 *   visible     — v-model:visible
 *   scar        — null = create mode, object = edit mode
 *   farmId      — pre-selected farm UUID (create)
 *   farms       — array of { id, name } for farm selector (create mode only)
 *
 * Emits:
 *   update:visible
 *   saved — after successful create / update
 */

import { ref, computed, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import InputNumber from 'primevue/inputnumber'
import * as scarService from '@/services/scarService.js'
import * as farmService from '@/services/farmService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  scar: { type: Object, default: null },
  farmId: { type: String, default: null },
  farms: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()
const saving = ref(false)

const isEdit = computed(() => !!props.scar)
const dialogTitle = computed(() => isEdit.value ? 'Sửa Scar' : 'Tạo Scar mới')

// ── Form fields ───────────────────────────────────────────────
const form = ref(emptyForm())
const areas = ref([])
const loadingAreas = ref(false)

function emptyForm() {
  return {
    farm_id: null,
    scar_type: null,
    title: '',
    description: '',
    source_of_risk: '',
    confidence_level: null,
    event_date: null,
    x_percent: null,
    y_percent: null,
    area_id: null,
  }
}

watch(() => props.visible, (val) => {
  if (!val) return
  if (isEdit.value) {
    form.value = {
      farm_id: props.scar.farm_id,
      scar_type: props.scar.scar_type,
      title: props.scar.title,
      description: props.scar.description || '',
      source_of_risk: props.scar.source_of_risk || '',
      confidence_level: props.scar.confidence_level,
      event_date: props.scar.event_date ? new Date(props.scar.event_date) : null,
      x_percent: props.scar.x_percent,
      y_percent: props.scar.y_percent,
      area_id: props.scar.area_id,
    }
    loadAreas(props.scar.farm_id)
  } else {
    form.value = emptyForm()
    form.value.farm_id = props.farmId
    if (props.farmId) loadAreas(props.farmId)
  }
})

watch(() => form.value.farm_id, (farmId) => {
  if (farmId) loadAreas(farmId)
  else areas.value = []
})

async function loadAreas(farmId) {
  if (!farmId) return
  loadingAreas.value = true
  try {
    const result = await farmService.listAreas(farmId)
    areas.value = (result || []).map(a => ({ label: a.name, value: a.id }))
  } catch {
    areas.value = []
  } finally {
    loadingAreas.value = false
  }
}

// ── Options ───────────────────────────────────────────────────
const scarTypeOptions = [
  { label: 'Ổ dịch', value: 'outbreak' },
  { label: 'Hotspot', value: 'hotspot' },
  { label: 'Vi phạm lặp lại', value: 'repeated_breach' },
  { label: 'Suýt xảy ra', value: 'near_miss' },
  { label: 'Lỗi cấu trúc', value: 'structural_flaw' },
]

const confidenceOptions = [
  { label: 'Nghi ngờ', value: 'suspected' },
  { label: 'Có thể', value: 'probable' },
  { label: 'Xác nhận', value: 'confirmed' },
]

// ── Validation ────────────────────────────────────────────────
const formValid = computed(() => {
  return form.value.farm_id && form.value.scar_type && form.value.title.trim() && form.value.description.trim() && form.value.confidence_level
})

// ── Save ──────────────────────────────────────────────────────
async function onSave() {
  if (!formValid.value) return
  saving.value = true
  try {
    const payload = {
      ...form.value,
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      source_of_risk: form.value.source_of_risk?.trim() || null,
      event_date: form.value.event_date ? formatDateISO(form.value.event_date) : null,
    }
    // Clean up nulls for update
    if (isEdit.value) {
      const updatePayload = {}
      if (payload.title !== props.scar.title) updatePayload.title = payload.title
      if (payload.description !== (props.scar.description || '')) updatePayload.description = payload.description
      if (payload.source_of_risk !== (props.scar.source_of_risk || null)) updatePayload.source_of_risk = payload.source_of_risk
      if (payload.confidence_level !== props.scar.confidence_level) updatePayload.confidence_level = payload.confidence_level
      if (payload.x_percent !== props.scar.x_percent) updatePayload.x_percent = payload.x_percent
      if (payload.y_percent !== props.scar.y_percent) updatePayload.y_percent = payload.y_percent

      await scarService.updateScar(props.scar.id, updatePayload)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã cập nhật scar', life: 3000 })
    } else {
      await scarService.createScar(payload)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo scar mới', life: 3000 })
    }

    emit('saved')
    emit('update:visible', false)
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.message || 'Không thể lưu scar'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 4000 })
  } finally {
    saving.value = false
  }
}

function formatDateISO(d) {
  if (!d) return null
  return d instanceof Date ? d.toISOString().split('T')[0] : d
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
    :closeOnEscape="!saving"
  >
    <div class="scar-form">
      <!-- Farm (create only) -->
      <div class="form-row" v-if="!isEdit">
        <label>Trại <span class="required">*</span></label>
        <Select
          v-model="form.farm_id"
          :options="farms"
          optionLabel="name"
          optionValue="id"
          placeholder="Chọn trại"
          filter
          class="w-full"
        />
      </div>

      <!-- Scar type -->
      <div class="form-row">
        <label>Loại scar <span class="required">*</span></label>
        <Select
          v-model="form.scar_type"
          :options="scarTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn loại"
          class="w-full"
          :disabled="isEdit"
        />
      </div>

      <!-- Title -->
      <div class="form-row">
        <label>Tiêu đề <span class="required">*</span></label>
        <InputText v-model="form.title" placeholder="Nhập tiêu đề" class="w-full" />
      </div>

      <!-- Description -->
      <div class="form-row">
        <label>Mô tả <span class="required">*</span></label>
        <Textarea v-model="form.description" placeholder="Mô tả chi tiết vết sẹo rủi ro" rows="3" class="w-full" />
      </div>

      <!-- Source of risk -->
      <div class="form-row">
        <label>Nguồn rủi ro</label>
        <InputText v-model="form.source_of_risk" placeholder="VD: Đường vận chuyển, ao nuôi..." class="w-full" />
      </div>

      <!-- Confidence level -->
      <div class="form-row">
        <label>Độ tin cậy <span class="required">*</span></label>
        <Select
          v-model="form.confidence_level"
          :options="confidenceOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn mức"
          class="w-full"
        />
      </div>

      <!-- Event date -->
      <div class="form-row">
        <label>Ngày sự kiện</label>
        <DatePicker
          v-model="form.event_date"
          dateFormat="dd/mm/yy"
          placeholder="Chọn ngày"
          class="w-full"
          :manualInput="false"
          showButtonBar
        />
      </div>

      <!-- Position -->
      <div class="form-row-pair">
        <div class="form-row half">
          <label>X (%)</label>
          <InputNumber v-model="form.x_percent" :min="0" :max="100" :maxFractionDigits="2" placeholder="0–100" class="w-full" />
        </div>
        <div class="form-row half">
          <label>Y (%)</label>
          <InputNumber v-model="form.y_percent" :min="0" :max="100" :maxFractionDigits="2" placeholder="0–100" class="w-full" />
        </div>
      </div>

      <!-- Area -->
      <div class="form-row" v-if="areas.length > 0">
        <label>Khu vực</label>
        <Select
          v-model="form.area_id"
          :options="areas"
          optionLabel="label"
          optionValue="value"
          placeholder="Chọn khu vực (tuỳ chọn)"
          class="w-full"
          showClear
          :loading="loadingAreas"
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <Button label="Huỷ" severity="secondary" text @click="emit('update:visible', false)" :disabled="saving" />
        <Button :label="isEdit ? 'Cập nhật' : 'Tạo'" icon="pi pi-check" :loading="saving" :disabled="!formValid" @click="onSave" />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.scar-form {
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
.form-row-pair {
  display: flex;
  gap: 1rem;
}
.form-row.half {
  flex: 1;
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
