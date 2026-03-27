<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import InputSwitch from 'primevue/inputswitch'
import { useKillerMetricStore } from '@/stores/killerMetric.js'

const toast = useToast()
const store = useKillerMetricStore()

const showDialog = ref(false)
const editing = ref(null)
const form = ref(emptyForm())

const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
]

const priorityOptions = [
  { label: 'P0', value: 'P0' },
  { label: 'P1', value: 'P1' },
  { label: 'P2', value: 'P2' },
]

const sourceTypeOptions = [
  { label: 'Từ scorecard item', value: 'scorecard_item' },
  { label: 'Từ báo cáo thực địa', value: 'field_report' },
  { label: 'Cả hai nguồn', value: 'both' },
]

function sourceTypeLabel(val) {
  const m = { scorecard_item: 'Scorecard Item', field_report: 'Báo cáo thực địa', both: 'Cả hai' }
  return m[val] || val
}

function sourceTypeColor(val) {
  const m = { scorecard_item: 'info', field_report: 'warn', both: 'success' }
  return m[val] || 'secondary'
}

function emptyForm() {
  return { code: '', name: '', description: '', severity_level: 'critical', default_case_priority: 'P0', active_flag: true, source_type: 'both' }
}

function severityColor(level) {
  const m = { critical: 'danger', high: 'warn', medium: 'info' }
  return m[level] || 'secondary'
}

function openCreate() {
  editing.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row) {
  editing.value = row
  form.value = {
    code: row.code,
    name: row.name,
    description: row.description || '',
    severity_level: row.severity_level,
    default_case_priority: row.default_case_priority,
    active_flag: row.active_flag,
    source_type: row.source_type || 'both',
  }
  showDialog.value = true
}

async function save() {
  try {
    if (editing.value) {
      await store.updateDefinition(editing.value.id, {
        name: form.value.name,
        description: form.value.description || null,
        severity_level: form.value.severity_level,
        default_case_priority: form.value.default_case_priority,
        active_flag: form.value.active_flag,
        source_type: form.value.source_type,
      })
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã cập nhật định nghĩa', life: 3000 })
    } else {
      await store.createDefinition(form.value)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo định nghĩa mới', life: 3000 })
    }
    showDialog.value = false
  } catch (e) {
    const msg = e.response?.data?.error?.message || 'Có lỗi xảy ra'
    toast.add({ severity: 'error', summary: 'Lỗi', detail: msg, life: 5000 })
  }
}

onMounted(() => store.fetchDefinitions())
</script>

<template>
  <Toast />
  <div class="km-def-page">
    <div class="page-header">
      <div>
        <h2><i class="pi pi-exclamation-circle" style="color: var(--p-red-500)"></i> Killer Metric Definitions</h2>
        <p class="subtitle">Quản lý danh sách các chỉ số killer — vi phạm nghiêm trọng cần bắt buộc mở case</p>
      </div>
      <Button label="Thêm định nghĩa" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable
      :value="store.definitions"
      :loading="store.definitionsLoading"
      stripedRows
      class="def-table"
    >
      <Column field="code" header="Mã" style="width: 160px">
        <template #body="{ data }">
          <code class="code-badge">{{ data.code }}</code>
        </template>
      </Column>
      <Column field="name" header="Tên" />
      <Column field="severity_level" header="Mức độ" style="width: 120px">
        <template #body="{ data }">
          <Tag :value="data.severity_level" :severity="severityColor(data.severity_level)" />
        </template>
      </Column>
      <Column field="default_case_priority" header="Ưu tiên" style="width: 100px">
        <template #body="{ data }">
          <Tag :value="data.default_case_priority" severity="contrast" />
        </template>
      </Column>
      <Column field="source_type" header="Nguồn" style="width: 160px">
        <template #body="{ data }">
          <Tag :value="sourceTypeLabel(data.source_type)" :severity="sourceTypeColor(data.source_type)" />
        </template>
      </Column>
      <Column field="active_flag" header="Trạng thái" style="width: 110px">
        <template #body="{ data }">
          <Tag :value="data.active_flag ? 'Active' : 'Inactive'" :severity="data.active_flag ? 'success' : 'secondary'" />
        </template>
      </Column>
      <Column header="" style="width: 80px">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text rounded severity="secondary" @click="openEdit(data)" />
        </template>
      </Column>
      <template #empty>
        <div class="empty-msg">Chưa có định nghĩa killer metric nào.</div>
      </template>
    </DataTable>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="editing ? 'Sửa định nghĩa' : 'Thêm định nghĩa'"
      modal
      :style="{ width: '520px' }"
    >
      <div class="form-grid">
        <div class="form-field" v-if="!editing">
          <label>Mã (code)</label>
          <InputText v-model="form.code" placeholder="VD: RED_LINE_BREACH" class="w-full" />
        </div>
        <div class="form-field">
          <label>Tên</label>
          <InputText v-model="form.name" placeholder="Tên hiển thị" class="w-full" />
        </div>
        <div class="form-field">
          <label>Mô tả</label>
          <Textarea v-model="form.description" rows="3" class="w-full" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Mức độ</label>
            <Select v-model="form.severity_level" :options="severityOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="form-field">
            <label>Ưu tiên mặc định</label>
            <Select v-model="form.default_case_priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="form-field">
          <label>Nguồn kích hoạt</label>
          <Select v-model="form.source_type" :options="sourceTypeOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="form-field" v-if="editing">
          <label>Active</label>
          <InputSwitch v-model="form.active_flag" />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showDialog = false" />
        <Button :label="editing ? 'Cập nhật' : 'Tạo'" icon="pi pi-check" @click="save" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.km-def-page { width: 100%; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h2 {
  margin: 0 0 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.3rem;
}

.subtitle {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin: 0;
}

.code-badge {
  background: var(--p-surface-border);
  color: var(--p-text-color);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.empty-msg {
  text-align: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-field label {
  font-weight: 600;
  font-size: 0.85rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.w-full { width: 100%; }
</style>
