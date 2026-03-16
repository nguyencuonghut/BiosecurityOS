<script setup>
import { ref, watch, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useFarmStore } from '@/stores/farm.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  farm: { type: Object, default: null },
  regions: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()
const farmStore = useFarmStore()

const isEdit = computed(() => !!props.farm?.id)
const dialogTitle = computed(() => (isEdit.value ? 'Chỉnh sửa trại' : 'Thêm trại mới'))

const form = ref({})
const saving = ref(false)
const errorMsg = ref('')

const farmTypeOptions = [
  { label: 'Nái', value: 'sow' },
  { label: 'Thịt', value: 'finisher' },
  { label: 'Hỗn hợp', value: 'mixed' },
  { label: 'Khác', value: 'other' },
]

const ownershipOptions = [
  { label: 'Công ty', value: 'company' },
  { label: 'Thuê', value: 'lease' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Khác', value: 'other' },
]

const statusOptions = [
  { label: 'Hoạt động', value: 'active' },
  { label: 'Tạm dừng', value: 'paused' },
  { label: 'Đã đóng', value: 'closed' },
  { label: 'Lưu trữ', value: 'archived' },
]

const riskOptions = [
  { label: 'Thấp', value: 'low' },
  { label: 'Trung bình', value: 'medium' },
  { label: 'Cao', value: 'high' },
  { label: 'Nghiêm trọng', value: 'critical' },
]

function resetForm() {
  if (props.farm) {
    form.value = {
      code: props.farm.code || '',
      name: props.farm.name || '',
      farm_type: props.farm.farm_type || 'sow',
      ownership_type: props.farm.ownership_type || 'company',
      region_id: props.farm.region_id || null,
      address: props.farm.address || '',
      latitude: props.farm.latitude,
      longitude: props.farm.longitude,
      capacity_headcount: props.farm.capacity_headcount,
      operational_status: props.farm.operational_status || 'active',
      baseline_risk_level: props.farm.baseline_risk_level || 'medium',
      structural_risk_note: props.farm.structural_risk_note || '',
      opened_at: props.farm.opened_at ? new Date(props.farm.opened_at) : null,
      closed_at: props.farm.closed_at ? new Date(props.farm.closed_at) : null,
    }
  } else {
    form.value = {
      code: '',
      name: '',
      farm_type: 'sow',
      ownership_type: 'company',
      region_id: null,
      address: '',
      latitude: null,
      longitude: null,
      capacity_headcount: null,
      operational_status: 'active',
      baseline_risk_level: 'medium',
      structural_risk_note: '',
      opened_at: null,
      closed_at: null,
    }
  }
  errorMsg.value = ''
}

watch(() => props.visible, (val) => {
  if (val) resetForm()
})

function formatDate(d) {
  if (!d) return null
  const dt = new Date(d)
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function onSubmit() {
  errorMsg.value = ''
  if (!form.value.code?.trim() || !form.value.name?.trim() || !form.value.region_id) {
    errorMsg.value = 'Vui lòng nhập đầy đủ: Mã, Tên, Vùng.'
    return
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    payload.opened_at = formatDate(payload.opened_at)
    payload.closed_at = formatDate(payload.closed_at)

    if (isEdit.value) {
      delete payload.code // code is immutable on edit
    }

    await farmStore.saveFarm(payload, isEdit.value ? props.farm.id : null)
    emit('saved')
  } catch (err) {
    const detail = err.response?.data?.error?.message || err.response?.data?.detail
    errorMsg.value = detail || 'Lỗi khi lưu trại.'
  } finally {
    saving.value = false
  }
}

function onHide() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    :header="dialogTitle"
    modal
    :closable="true"
    :style="{ width: '42rem' }"
    @update:visible="onHide"
  >
    <Message v-if="errorMsg" severity="error" :closable="false" class="mb-3">{{ errorMsg }}</Message>

    <div class="form-grid">
      <div class="field" v-if="!isEdit">
        <label>Mã trại *</label>
        <InputText v-model="form.code" placeholder="VD: FARM-001" :fluid="true" />
      </div>
      <div class="field">
        <label>Tên trại *</label>
        <InputText v-model="form.name" placeholder="Tên trại" :fluid="true" />
      </div>
      <div class="field">
        <label>Vùng *</label>
        <Select
          v-model="form.region_id"
          :options="regions"
          optionLabel="name"
          optionValue="id"
          placeholder="Chọn vùng"
          :fluid="true"
        />
      </div>
      <div class="field">
        <label>Loại trại</label>
        <Select
          v-model="form.farm_type"
          :options="farmTypeOptions"
          optionLabel="label"
          optionValue="value"
          :fluid="true"
        />
      </div>
      <div class="field">
        <label>Sở hữu</label>
        <Select
          v-model="form.ownership_type"
          :options="ownershipOptions"
          optionLabel="label"
          optionValue="value"
          :fluid="true"
        />
      </div>
      <div class="field">
        <label>Trạng thái</label>
        <Select
          v-model="form.operational_status"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          :fluid="true"
        />
      </div>
      <div class="field">
        <label>Mức rủi ro</label>
        <Select
          v-model="form.baseline_risk_level"
          :options="riskOptions"
          optionLabel="label"
          optionValue="value"
          :fluid="true"
        />
      </div>
      <div class="field">
        <label>Công suất (đầu con)</label>
        <InputNumber v-model="form.capacity_headcount" :min="0" :fluid="true" />
      </div>
      <div class="field full-width">
        <label>Địa chỉ</label>
        <InputText v-model="form.address" placeholder="Địa chỉ" :fluid="true" />
      </div>
      <div class="field">
        <label>Vĩ độ</label>
        <InputNumber v-model="form.latitude" :minFractionDigits="4" :maxFractionDigits="8" :min="-90" :max="90" :fluid="true" />
      </div>
      <div class="field">
        <label>Kinh độ</label>
        <InputNumber v-model="form.longitude" :minFractionDigits="4" :maxFractionDigits="8" :min="-180" :max="180" :fluid="true" />
      </div>
      <div class="field">
        <label>Ngày mở</label>
        <DatePicker v-model="form.opened_at" dateFormat="dd/mm/yy" :fluid="true" />
      </div>
      <div class="field">
        <label>Ngày đóng</label>
        <DatePicker v-model="form.closed_at" dateFormat="dd/mm/yy" :fluid="true" />
      </div>
      <div class="field full-width">
        <label>Ghi chú rủi ro cấu trúc</label>
        <Textarea v-model="form.structural_risk_note" rows="2" :fluid="true" />
      </div>
    </div>

    <template #footer>
      <Button label="Hủy" severity="secondary" text @click="onHide" />
      <Button :label="isEdit ? 'Cập nhật' : 'Tạo mới'" icon="pi pi-check" :loading="saving" @click="onSubmit" />
    </template>
  </Dialog>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field label {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--p-text-color);
}

.full-width {
  grid-column: 1 / -1;
}

.mb-3 {
  margin-bottom: 0.75rem;
}
</style>
