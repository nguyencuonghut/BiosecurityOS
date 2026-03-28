<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const props = defineProps({
  farmId: { type: String, required: true },
})

const toast = useToast()
const farmStore = useFarmStore()
const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermission('FARM_WRITE'))

const showDialog = ref(false)
const saving = ref(false)
const errorMsg = ref('')

const form = ref({
  risk_type: '',
  name: '',
  latitude: null,
  longitude: null,
  distance_m: null,
  note: '',
  confidence_level: 'suspected',
})

const riskTypeOptions = [
  { label: 'Chợ gia súc', value: 'market' },
  { label: 'Bãi rác', value: 'dump' },
  { label: 'Lò mổ', value: 'slaughterhouse' },
  { label: 'Khu tiêu hủy', value: 'disposal_site' },
  { label: 'Ao nước thải', value: 'wastewater' },
  { label: 'Trại chăn nuôi lân cận', value: 'farm' },
  { label: 'Nguồn nước', value: 'water_source' },
  { label: 'Đường giao thông lớn', value: 'road' },
  { label: 'Khác', value: 'other' },
]

const confidenceOptions = [
  { label: 'Nghi ngờ', value: 'suspected' },
  { label: 'Có thể', value: 'probable' },
  { label: 'Xác nhận', value: 'confirmed' },
]

function openCreate() {
  form.value = { risk_type: null, name: '', latitude: null, longitude: null, distance_m: null, note: '', confidence_level: 'suspected' }
  errorMsg.value = ''
  showDialog.value = true
}

async function onSubmit() {
  errorMsg.value = ''
  if (!form.value.risk_type || form.value.latitude == null || form.value.longitude == null) {
    errorMsg.value = 'Vui lòng nhập: Loại rủi ro, Vĩ độ, Kinh độ.'
    return
  }

  saving.value = true
  try {
    await farmStore.saveRiskPoint(props.farmId, form.value)
    showDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm điểm rủi ro', life: 3000 })
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Lỗi khi tạo điểm rủi ro.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="risk-panel">
    <div class="panel-header">
      <span class="panel-title">Điểm rủi ro bên ngoài</span>
      <Button
        v-if="canWrite"
        label="Thêm điểm"
        icon="pi pi-plus"
        size="small"
        @click="openCreate"
      />
    </div>

    <DataTable :value="farmStore.riskPoints" stripedRows v-if="farmStore.riskPoints.length">
      <Column header="Loại" style="width: 10rem">
        <template #body="{ data }">{{ data.risk_type_label }}</template>
      </Column>
      <Column header="Tên" field="name" />
      <Column header="Khoảng cách" style="width: 8rem">
        <template #body="{ data }">{{ data.distance_m != null ? `${data.distance_m}m` : '—' }}</template>
      </Column>
      <Column header="Tọa độ" style="width: 12rem">
        <template #body="{ data }">{{ data.latitude }}, {{ data.longitude }}</template>
      </Column>
      <Column header="Mức tin cậy" style="width: 8rem">
        <template #body="{ data }"><StatusBadge :value="data.confidence_level" type="confidence" /></template>
      </Column>
      <Column header="Ghi chú" field="note" />
    </DataTable>

    <div v-else class="empty-msg">Chưa có điểm rủi ro nào.</div>

    <Dialog
      :visible="showDialog"
      header="Thêm điểm rủi ro"
      modal
      :style="{ width: '30rem' }"
      @update:visible="showDialog = $event"
    >
      <div class="form-fields">
        <div class="field">
          <label>Loại rủi ro *</label>
          <Select v-model="form.risk_type" :options="riskTypeOptions" optionLabel="label" optionValue="value" placeholder="Chọn loại rủi ro" :fluid="true" />
        </div>
        <div class="field">
          <label>Tên</label>
          <InputText v-model="form.name" placeholder="Tên điểm" :fluid="true" />
        </div>
        <div class="field-row-2">
          <div class="field">
            <label>Vĩ độ *</label>
            <InputNumber v-model="form.latitude" :minFractionDigits="4" :maxFractionDigits="8" :min="-90" :max="90" :fluid="true" />
          </div>
          <div class="field">
            <label>Kinh độ *</label>
            <InputNumber v-model="form.longitude" :minFractionDigits="4" :maxFractionDigits="8" :min="-180" :max="180" :fluid="true" />
          </div>
        </div>
        <div class="field">
          <label>Khoảng cách (m)</label>
          <InputNumber v-model="form.distance_m" :min="0" :fluid="true" />
        </div>
        <div class="field">
          <label>Mức tin cậy</label>
          <Select v-model="form.confidence_level" :options="confidenceOptions" optionLabel="label" optionValue="value" :fluid="true" />
        </div>
        <div class="field">
          <label>Ghi chú</label>
          <Textarea v-model="form.note" rows="2" :fluid="true" />
        </div>
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showDialog = false" />
        <Button label="Tạo" icon="pi pi-check" :loading="saving" @click="onSubmit" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.panel-title { font-weight: 600; font-size: 0.95rem; }
.form-fields { display: flex; flex-direction: column; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field label { font-weight: 600; font-size: 0.85rem; }
.field-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.error-msg { color: var(--p-red-500); font-size: 0.85rem; }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }
</style>
