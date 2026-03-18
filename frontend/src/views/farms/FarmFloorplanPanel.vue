<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'
import { useAuthStore } from '@/stores/auth.js'
import * as floorplanService from '@/services/floorplanService.js'

const props = defineProps({
  farmId: { type: String, required: true },
})

const toast = useToast()
const authStore = useAuthStore()

const floorplans = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)

const form = ref({
  title: '',
  effective_from: null,
})

onMounted(() => fetchFloorplans())

async function fetchFloorplans() {
  loading.value = true
  try {
    floorplans.value = await floorplanService.listFloorplans(props.farmId)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { title: '', effective_from: null }
  showCreateDialog.value = true
}

async function submitCreate() {
  if (!form.value.title || !form.value.effective_from) return
  creating.value = true
  try {
    const effectiveFrom = form.value.effective_from instanceof Date
      ? form.value.effective_from.toISOString().split('T')[0]
      : form.value.effective_from
    await floorplanService.createFloorplan(props.farmId, {
      title: form.value.title,
      effective_from: effectiveFrom,
    })
    showCreateDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo floorplan mới', life: 3000 })
    await fetchFloorplans()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể tạo', life: 4000 })
  } finally {
    creating.value = false
  }
}

async function approveFloorplan(fp) {
  try {
    await floorplanService.approveFloorplan(fp.id)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã kích hoạt floorplan', life: 3000 })
    await fetchFloorplans()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.message || 'Không thể kích hoạt', life: 4000 })
  }
}

function statusSeverity(status) {
  return { draft: 'warn', active: 'success', archived: 'secondary' }[status] || 'info'
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('vi-VN')
}
</script>

<template>
  <div class="floorplan-panel">
    <div class="panel-toolbar">
      <h3>Danh sách Floorplan</h3>
      <Button
        v-if="authStore.hasPermission('SCAR_WRITE')"
        label="Tạo phiên bản"
        icon="pi pi-plus"
        size="small"
        @click="openCreate"
      />
    </div>

    <DataTable :value="floorplans" :loading="loading" stripedRows size="small" :paginator="false">
      <template #empty>Chưa có floorplan nào.</template>
      <Column field="version_no" header="Phiên bản" style="width: 80px">
        <template #body="{ data }">v{{ data.version_no }}</template>
      </Column>
      <Column field="title" header="Tiêu đề" />
      <Column field="status" header="Trạng thái" style="width: 120px">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="statusSeverity(data.status)" />
        </template>
      </Column>
      <Column field="effective_from" header="Hiệu lực từ" style="width: 130px">
        <template #body="{ data }">{{ formatDate(data.effective_from) }}</template>
      </Column>
      <Column field="effective_to" header="Hiệu lực đến" style="width: 130px">
        <template #body="{ data }">{{ formatDate(data.effective_to) }}</template>
      </Column>
      <Column header="" style="width: 130px">
        <template #body="{ data }">
          <Button
            v-if="data.status === 'draft' && authStore.hasPermission('SCAR_WRITE')"
            label="Kích hoạt"
            icon="pi pi-check"
            size="small"
            severity="success"
            text
            @click="approveFloorplan(data)"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Create dialog -->
    <Dialog v-model:visible="showCreateDialog" header="Tạo Floorplan mới" modal :style="{ width: '30rem' }">
      <div class="form-grid">
        <div class="form-field">
          <label>Tiêu đề *</label>
          <InputText v-model="form.title" class="w-full" placeholder="VD: Mặt bằng v2 — cải tạo 2026" />
        </div>
        <div class="form-field">
          <label>Hiệu lực từ *</label>
          <DatePicker v-model="form.effective_from" dateFormat="dd/mm/yy" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showCreateDialog = false" />
        <Button label="Tạo" icon="pi pi-check" :loading="creating" @click="submitCreate" :disabled="!form.title || !form.effective_from" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.panel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.panel-toolbar h3 {
  margin: 0;
  font-size: 1.1rem;
}
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.form-field label {
  font-weight: 600;
  font-size: 0.875rem;
}
</style>
