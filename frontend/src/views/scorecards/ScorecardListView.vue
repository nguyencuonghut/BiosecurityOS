<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScorecardStore } from '@/stores/scorecard.js'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Calendar from 'primevue/calendar'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const store = useScorecardStore()
const toast = useToast()

const showCreateDialog = ref(false)
const formData = ref({
  code: '',
  name: '',
  farm_type: null,
  ownership_type: null,
  risk_profile: null,
  version_no: 1,
  effective_from: null,
  effective_to: null,
})

const farmTypeOptions = [
  { label: 'Nái', value: 'sow' },
  { label: 'Thịt', value: 'finisher' },
  { label: 'Hỗn hợp', value: 'mixed' },
  { label: 'Khác', value: 'other' },
]

const statusOptions = [
  { label: 'Nháp', value: 'draft' },
  { label: 'Đang dùng', value: 'active' },
  { label: 'Lưu trữ', value: 'archived' },
]

onMounted(() => {
  store.fetchTemplates()
})

function onPage(event) {
  store.filters.page = event.page + 1
  store.filters.page_size = event.rows
  store.fetchTemplates()
}

function onFilterChange() {
  store.filters.page = 1
  store.fetchTemplates()
}

function resetForm() {
  formData.value = {
    code: '', name: '', farm_type: null, ownership_type: null,
    risk_profile: null, version_no: 1, effective_from: null, effective_to: null,
  }
}

function formatDate(d) {
  if (!d) return null
  const dt = d instanceof Date ? d : new Date(d)
  return dt.toISOString().split('T')[0]
}

async function handleCreate() {
  try {
    const payload = {
      ...formData.value,
      effective_from: formatDate(formData.value.effective_from),
      effective_to: formatDate(formData.value.effective_to),
    }
    await store.saveTemplate(payload)
    showCreateDialog.value = false
    resetForm()
    store.fetchTemplates()
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo template', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Không thể tạo template', life: 5000 })
  }
}

function openBuilder(row) {
  router.push(`/scorecards/${row.id}`)
}
</script>

<template>
  <div class="scorecard-list">
    <div class="page-header">
      <h2>Quản lý Scorecard Templates</h2>
      <Button label="Tạo Template" icon="pi pi-plus" @click="showCreateDialog = true" />
    </div>

    <div class="filter-bar">
      <Select
        v-model="store.filters.farm_type"
        :options="farmTypeOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Loại trại"
        showClear
        @change="onFilterChange"
      />
      <Select
        v-model="store.filters.status"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Trạng thái"
        showClear
        @change="onFilterChange"
      />
    </div>

    <DataTable
      :value="store.templates"
      :loading="store.loading"
      :totalRecords="store.totalRecords"
      :rows="store.filters.page_size"
      :lazy="true"
      paginator
      @page="onPage"
      stripedRows
      class="mt-3"
    >
      <Column field="code" header="Mã" style="width: 12%">
        <template #body="{ data }">
          <a class="link" @click="openBuilder(data)">{{ data.code }}</a>
        </template>
      </Column>
      <Column field="name" header="Tên template" style="width: 28%" />
      <Column field="farm_type" header="Loại trại" style="width: 10%">
        <template #body="{ data }">
          {{ farmTypeOptions.find(o => o.value === data.farm_type)?.label || data.farm_type || '—' }}
        </template>
      </Column>
      <Column field="version_no" header="Version" style="width: 8%" />
      <Column field="status" header="Trạng thái" style="width: 10%">
        <template #body="{ data }">
          <StatusBadge :value="data.status" />
        </template>
      </Column>
      <Column field="effective_from" header="Hiệu lực từ" style="width: 12%" />
      <Column field="effective_to" header="Đến" style="width: 10%">
        <template #body="{ data }">{{ data.effective_to || '—' }}</template>
      </Column>
      <Column header="" style="width: 10%">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text rounded size="small" @click="openBuilder(data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateDialog" header="Tạo Scorecard Template" :modal="true" style="width: 32rem">
      <div class="form-grid">
        <div class="field">
          <label>Mã template *</label>
          <InputText v-model="formData.code" placeholder="TMPL-001" class="w-full" />
        </div>
        <div class="field">
          <label>Tên *</label>
          <InputText v-model="formData.name" placeholder="Tên template" class="w-full" />
        </div>
        <div class="field">
          <label>Loại trại</label>
          <Select v-model="formData.farm_type" :options="farmTypeOptions" optionLabel="label" optionValue="value" placeholder="Chọn" showClear class="w-full" />
        </div>
        <div class="field">
          <label>Version *</label>
          <InputNumber v-model="formData.version_no" :min="1" class="w-full" />
        </div>
        <div class="field">
          <label>Hiệu lực từ *</label>
          <Calendar v-model="formData.effective_from" dateFormat="yy-mm-dd" class="w-full" />
        </div>
        <div class="field">
          <label>Đến</label>
          <Calendar v-model="formData.effective_to" dateFormat="yy-mm-dd" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" text @click="showCreateDialog = false" />
        <Button label="Tạo" icon="pi pi-check" @click="handleCreate" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.filter-bar {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}
.field label {
  font-weight: 600;
  font-size: 0.875rem;
}
.link {
  color: var(--p-primary-color);
  cursor: pointer;
  font-weight: 600;
}
.link:hover {
  text-decoration: underline;
}
.mt-3 { margin-top: 0.75rem; }
</style>
