<script setup>
/**
 * ScarFormDialog.vue — Create / Edit scar dialog.
 *
 * Props:
 *   visible     — v-model:visible
 *   scar        — null = create mode, object = edit mode
 *   farmId      — pre-selected farm UUID (create)
 *   farms       — array of { id, name } for farm selector (create mode only)
 *   initialX    — pre-filled x_percent from canvas click
 *   initialY    — pre-filled y_percent from canvas click
 *   floorplanImageUrl — image URL for the minimap picker
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
import * as attachmentService from '@/services/attachmentService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  scar: { type: Object, default: null },
  farmId: { type: String, default: null },
  farms: { type: Array, default: () => [] },
  initialX: { type: Number, default: null },
  initialY: { type: Number, default: null },
  floorplanImageUrl: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()
const saving = ref(false)

const isEdit = computed(() => !!props.scar)
const dialogTitle = computed(() => isEdit.value ? 'Sửa Scar' : 'Tạo Scar mới')

// ── Minimap picker ────────────────────────────────────────────
const minimapRef = ref(null)
const minimapImageUrl = ref(null)
const loadingMinimap = ref(false)

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
    loadMinimapImage(props.scar.farm_id)
  } else {
    form.value = emptyForm()
    form.value.farm_id = props.farmId
    if (props.initialX != null) form.value.x_percent = props.initialX
    if (props.initialY != null) form.value.y_percent = props.initialY
    if (props.farmId) {
      loadAreas(props.farmId)
      loadMinimapImage(props.farmId)
    }
  }
})

watch(() => form.value.farm_id, (farmId) => {
  if (farmId) {
    loadAreas(farmId)
    loadMinimapImage(farmId)
  } else {
    areas.value = []
    minimapImageUrl.value = null
  }
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

// ── Minimap image loading ─────────────────────────────────────
async function loadMinimapImage(farmId) {
  // Use the prop if provided (from ScarMapView)
  if (props.floorplanImageUrl) {
    minimapImageUrl.value = props.floorplanImageUrl
    return
  }
  // Otherwise, fetch the active floorplan for this farm
  minimapImageUrl.value = null
  loadingMinimap.value = true
  try {
    const scarMapData = await scarService.getScarMap(farmId)
    if (scarMapData?.floorplan?.plan_file_attachment_id) {
      const result = await attachmentService.getViewUrl(scarMapData.floorplan.plan_file_attachment_id)
      minimapImageUrl.value = result.view_url
    }
  } catch {
    // no floorplan available
  } finally {
    loadingMinimap.value = false
  }
}

function onMinimapClick(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * 100
  const y = ((event.clientY - rect.top) / rect.height) * 100
  form.value.x_percent = Math.round(x * 10) / 10
  form.value.y_percent = Math.round(y * 10) / 10
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
    :style="{ width: '44rem' }"
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

      <!-- Position picker -->
      <div class="form-row">
        <label>Vị trí trên sơ đồ mặt bằng</label>
        <div class="minimap-picker" v-if="minimapImageUrl" ref="minimapRef" @click="onMinimapClick">
          <img :src="minimapImageUrl" class="minimap-image" alt="Floorplan" draggable="false" />
          <!-- Pin at selected position -->
          <div
            v-if="form.x_percent != null && form.y_percent != null"
            class="minimap-pin"
            :style="{ left: form.x_percent + '%', top: form.y_percent + '%' }"
          >
            <i class="pi pi-map-marker" />
          </div>
          <div class="minimap-hint">Click để chọn vị trí</div>
        </div>
        <div v-else-if="loadingMinimap" class="minimap-empty">
          <i class="pi pi-spin pi-spinner" />
          <span>Đang tải sơ đồ...</span>
        </div>
        <div v-else class="minimap-empty">
          <i class="pi pi-image" />
          <span>Chưa có ảnh sơ đồ mặt bằng — nhập toạ độ thủ công</span>
        </div>
      </div>

      <!-- X/Y coordinates (auto-filled from click, or manual) -->
      <div class="form-row-pair">
        <div class="form-row half">
          <label>X (%) {{ form.x_percent != null ? '' : '' }}</label>
          <InputNumber v-model="form.x_percent" :min="0" :max="100" :maxFractionDigits="1" placeholder="0–100" class="w-full" />
        </div>
        <div class="form-row half">
          <label>Y (%)</label>
          <InputNumber v-model="form.y_percent" :min="0" :max="100" :maxFractionDigits="1" placeholder="0–100" class="w-full" />
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

/* ── Minimap Picker ───────────────────────────────────── */
.minimap-picker {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  border: 2px solid var(--p-surface-300);
  border-radius: 8px;
  overflow: hidden;
  cursor: crosshair;
  background: var(--p-surface-100);
  transition: border-color 0.2s;
}
.minimap-picker:hover {
  border-color: var(--p-primary-color);
}
.minimap-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  user-select: none;
}
.minimap-pin {
  position: absolute;
  transform: translate(-50%, -100%);
  color: var(--p-red-500);
  font-size: 1.5rem;
  z-index: 5;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4));
  pointer-events: none;
  animation: pin-drop 0.3s ease-out;
}
@keyframes pin-drop {
  0% { transform: translate(-50%, -150%); opacity: 0; }
  100% { transform: translate(-50%, -100%); opacity: 1; }
}
.minimap-hint {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 0.7rem;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  pointer-events: none;
  white-space: nowrap;
}
.minimap-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem;
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
  background: var(--p-surface-50);
  border: 1px dashed var(--p-surface-300);
  border-radius: 8px;
}
.minimap-empty i {
  font-size: 1.25rem;
}
</style>
