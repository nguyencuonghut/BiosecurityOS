<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
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
  route_type: '',
  from_area_id: null,
  to_area_id: null,
  direction_rule: 'one_way',
  note: '',
})

const directionOptions = [
  { label: 'Một chiều', value: 'one_way' },
  { label: 'Hạn chế', value: 'restricted' },
  { label: 'Có điều kiện', value: 'conditional' },
  { label: 'Hai chiều', value: 'bidirectional' },
]

const areaOptions = computed(() =>
  farmStore.areas.map((a) => ({ label: `${a.code} — ${a.name}`, value: a.id }))
)

function areaName(areaId) {
  const a = farmStore.areas.find((a) => a.id === areaId)
  return a ? `${a.code} — ${a.name}` : areaId
}

function directionLabel(val) {
  const m = { one_way: 'Một chiều', restricted: 'Hạn chế', conditional: 'Có ĐK', bidirectional: 'Hai chiều' }
  return m[val] || val
}

function openCreate() {
  form.value = { route_type: '', from_area_id: null, to_area_id: null, direction_rule: 'one_way', note: '' }
  errorMsg.value = ''
  showDialog.value = true
}

async function onSubmit() {
  errorMsg.value = ''
  if (!form.value.route_type?.trim() || !form.value.from_area_id || !form.value.to_area_id) {
    errorMsg.value = 'Vui lòng nhập đầy đủ: Loại, Từ khu vực, Đến khu vực.'
    return
  }

  saving.value = true
  try {
    await farmStore.saveRoute(props.farmId, form.value)
    showDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm lộ trình', life: 3000 })
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Lỗi khi tạo lộ trình.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="route-panel">
    <div class="panel-header">
      <span class="panel-title">Danh sách lộ trình</span>
      <Button
        v-if="canWrite"
        label="Thêm lộ trình"
        icon="pi pi-plus"
        size="small"
        @click="openCreate"
      />
    </div>

    <DataTable :value="farmStore.routes" stripedRows v-if="farmStore.routes.length">
      <Column header="Loại" style="width: 8rem">
        <template #body="{ data }">{{ data.route_type_label }}</template>
      </Column>
      <Column header="Từ khu vực">
        <template #body="{ data }">{{ areaName(data.from_area_id) }}</template>
      </Column>
      <Column header="Đến khu vực">
        <template #body="{ data }">{{ areaName(data.to_area_id) }}</template>
      </Column>
      <Column header="Hướng" style="width: 8rem">
        <template #body="{ data }">
          <Tag :value="directionLabel(data.direction_rule)" severity="info" rounded />
        </template>
      </Column>
      <Column header="Ghi chú" field="note" />
    </DataTable>

    <div v-else class="empty-msg">Chưa có lộ trình nào.</div>

    <Dialog
      :visible="showDialog"
      header="Thêm lộ trình"
      modal
      :style="{ width: '28rem' }"
      @update:visible="showDialog = $event"
    >
      <div class="form-fields">
        <div class="field">
          <label>Loại lộ trình *</label>
          <InputText v-model="form.route_type" placeholder="VD: personnel, vehicle" :fluid="true" />
        </div>
        <div class="field">
          <label>Từ khu vực *</label>
          <Select v-model="form.from_area_id" :options="areaOptions" optionLabel="label" optionValue="value" placeholder="Chọn" :fluid="true" />
        </div>
        <div class="field">
          <label>Đến khu vực *</label>
          <Select v-model="form.to_area_id" :options="areaOptions" optionLabel="label" optionValue="value" placeholder="Chọn" :fluid="true" />
        </div>
        <div class="field">
          <label>Quy tắc hướng</label>
          <Select v-model="form.direction_rule" :options="directionOptions" optionLabel="label" optionValue="value" :fluid="true" />
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
.error-msg { color: var(--p-red-500); font-size: 0.85rem; }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }
</style>
