<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import {
  listAreaTypes,
  createAreaType,
  updateAreaType,
  deleteAreaType,
} from '@/services/farmService.js'

const toast = useToast()

const items = ref([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const editing = ref(null)
const errorMsg = ref('')
const searchQuery = ref('')

const filteredItems = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return items.value
  return items.value.filter(
    (r) => r.code.toLowerCase().includes(q) || r.name.toLowerCase().includes(q)
  )
})

const emptyForm = () => ({ code: '', name: '', display_order: 0 })
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    items.value = await listAreaTypes()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = emptyForm()
  errorMsg.value = ''
  showDialog.value = true
}

function openEdit(row) {
  editing.value = row
  form.value = { code: row.code, name: row.name, display_order: row.display_order }
  errorMsg.value = ''
  showDialog.value = true
}

async function onSave() {
  errorMsg.value = ''
  if (!form.value.code.trim() || !form.value.name.trim()) {
    errorMsg.value = 'Mã và Tên là bắt buộc.'
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateAreaType(editing.value.id, form.value)
      toast.add({ severity: 'success', summary: 'Đã cập nhật', life: 3000 })
    } else {
      await createAreaType(form.value)
      toast.add({ severity: 'success', summary: 'Đã tạo mới', life: 3000 })
    }
    showDialog.value = false
    await load()
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Có lỗi xảy ra.'
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  try {
    await deleteAreaType(row.id)
    toast.add({ severity: 'success', summary: `Đã xóa "${row.name}"`, life: 3000 })
    await load()
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Không thể xóa',
      detail: err.response?.data?.error?.message || 'Loại khu vực đang được sử dụng.',
      life: 5000,
    })
  }
}

onMounted(load)
</script>

<template>
  <div class="area-type-admin">
    <div class="page-header">
      <div>
        <h2 class="page-title">Cấu hình — Loại khu vực</h2>
        <p class="page-subtitle">Quản lý danh mục loại khu vực dùng trong quản lý trại.</p>
      </div>
      <Button label="Thêm mới" icon="pi pi-plus" @click="openCreate" />
    </div>

    <div class="table-toolbar">
      <IconField>
        <InputIcon class="pi pi-search" />
        <InputText v-model="searchQuery" placeholder="Tìm theo mã hoặc tên..." style="width: 18rem" />
      </IconField>
      <span class="result-count">{{ filteredItems.length }} / {{ items.length }} loại</span>
    </div>

    <DataTable
      :value="filteredItems"
      :loading="loading"
      stripedRows
      sortField="display_order"
      :sortOrder="1"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10, 20, 50]"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      class="area-type-table"
    >
      <Column header="Thứ tự" field="display_order" sortable style="width: 6rem; text-align: center" />
      <Column header="Mã" field="code" sortable style="width: 14rem">
        <template #body="{ data }">
          <span class="code-badge">{{ data.code }}</span>
        </template>
      </Column>
      <Column header="Tên hiển thị" field="name" sortable />
      <Column header="" style="width: 7rem; text-align: right">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text rounded size="small" @click="openEdit(data)" />
          <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="onDelete(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="showDialog"
      :header="editing ? 'Sửa loại khu vực' : 'Thêm loại khu vực'"
      modal
      :style="{ width: '24rem' }"
    >
      <div class="form-fields">
        <div class="field">
          <label>Mã (code) *</label>
          <InputText v-model="form.code" :disabled="!!editing" placeholder="VD: barn, gate, shower" :fluid="true" />
        </div>
        <div class="field">
          <label>Tên hiển thị *</label>
          <InputText v-model="form.name" placeholder="VD: Chuồng, Cổng, Nhà tắm" :fluid="true" />
        </div>
        <div class="field">
          <label>Thứ tự hiển thị</label>
          <InputNumber v-model="form.display_order" :min="0" :fluid="true" />
        </div>
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showDialog = false" />
        <Button
          :label="editing ? 'Cập nhật' : 'Tạo'"
          icon="pi pi-check"
          :loading="saving"
          @click="onSave"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.area-type-admin {
  padding: 1.5rem;
  width: 100%;
  box-sizing: border-box;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}
.page-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0 0 0.2rem;
}
.page-subtitle {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  margin: 0;
}
.code-badge {
  font-family: monospace;
  background: var(--p-primary-color);
  color: #fff;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.01em;
}
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.field label {
  font-weight: 600;
  font-size: 0.85rem;
}
.error-msg {
  color: var(--p-red-500);
  font-size: 0.85rem;
}
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.result-count {
  font-size: 0.82rem;
  color: var(--p-text-muted-color);
}
</style>
