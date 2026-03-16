<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import StatusBadge from '@/components/common/StatusBadge.vue'
import FarmFormDialog from '@/views/farms/FarmFormDialog.vue'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const toast = useToast()
const farmStore = useFarmStore()
const authStore = useAuthStore()

const showDialog = ref(false)
const editFarm = ref(null)

const farmTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Nái', value: 'sow' },
  { label: 'Thịt', value: 'finisher' },
  { label: 'Hỗn hợp', value: 'mixed' },
  { label: 'Khác', value: 'other' },
]

const ownershipOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Công ty', value: 'company' },
  { label: 'Thuê', value: 'lease' },
  { label: 'Hợp đồng', value: 'contract' },
  { label: 'Khác', value: 'other' },
]

const regionFilter = ref(null)
const farmTypeFilter = ref(null)
const ownershipFilter = ref(null)
const searchText = ref('')
let searchTimer = null

onMounted(async () => {
  await farmStore.fetchRegions()
  await farmStore.fetchFarms()
})

const regionOptions = ref([])
watch(
  () => farmStore.regions,
  (val) => {
    regionOptions.value = [{ label: 'Tất cả vùng', value: null }, ...val.map((r) => ({ label: r.name, value: r.id }))]
  },
  { immediate: true },
)

function onPage(event) {
  farmStore.filters.page = event.page + 1
  farmStore.filters.page_size = event.rows
  farmStore.fetchFarms()
}

function onSort(event) {
  const prefix = event.sortOrder === -1 ? '-' : ''
  farmStore.filters.sort = prefix + event.sortField
  farmStore.fetchFarms()
}

function applyFilters() {
  farmStore.filters.region_id = regionFilter.value
  farmStore.filters.farm_type = farmTypeFilter.value
  farmStore.filters.ownership_type = ownershipFilter.value
  farmStore.filters.page = 1
  farmStore.fetchFarms()
}

watch([regionFilter, farmTypeFilter, ownershipFilter], applyFilters)

watch(searchText, (val) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    farmStore.filters.search = val || null
    farmStore.filters.page = 1
    farmStore.fetchFarms()
  }, 400)
})

function openCreate() {
  editFarm.value = null
  showDialog.value = true
}

function openEdit(farm) {
  editFarm.value = { ...farm }
  showDialog.value = true
}

async function onSaved() {
  showDialog.value = false
  toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã lưu trại', life: 3000 })
  await farmStore.fetchFarms()
}

function goToDetail(farm) {
  router.push({ name: 'FarmDetail', params: { id: farm.id } })
}

function farmTypeLabel(val) {
  const m = { sow: 'Nái', finisher: 'Thịt', mixed: 'Hỗn hợp', other: 'Khác' }
  return m[val] || val
}

function ownershipLabel(val) {
  const m = { company: 'Công ty', lease: 'Thuê', contract: 'Hợp đồng', other: 'Khác' }
  return m[val] || val
}

function regionName(regionId) {
  const r = farmStore.regions.find((r) => r.id === regionId)
  return r?.name || regionId
}
</script>

<template>
  <Toast />
  <div class="farm-list">
    <div class="page-header">
      <h2>Danh sách trại</h2>
      <Button
        v-if="authStore.hasPermission('FARM_WRITE')"
        label="Thêm trại"
        icon="pi pi-plus"
        @click="openCreate"
      />
    </div>

    <DataTable
      :value="farmStore.farms"
      :totalRecords="farmStore.totalRecords"
      :loading="farmStore.loading"
      :rows="farmStore.filters.page_size"
      :rowsPerPageOptions="[10, 20, 50]"
      paginator
      lazy
      stripedRows
      removableSort
      @page="onPage"
      @sort="onSort"
      @row-click="(e) => goToDetail(e.data)"
      selectionMode="single"
      class="farm-table"
    >
      <template #header>
        <div class="filter-bar">
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText v-model="searchText" placeholder="Tìm kiếm trại..." />
          </IconField>
          <Select
            v-model="regionFilter"
            :options="regionOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Vùng"
            class="filter-select"
          />
          <Select
            v-model="farmTypeFilter"
            :options="farmTypeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Loại trại"
            class="filter-select"
          />
          <Select
            v-model="ownershipFilter"
            :options="ownershipOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Sở hữu"
            class="filter-select"
          />
        </div>
      </template>

      <Column field="code" header="Mã" sortable style="width: 8rem" />
      <Column field="name" header="Tên trại" sortable style="min-width: 14rem" />
      <Column field="region_id" header="Vùng" style="width: 10rem">
        <template #body="{ data }">{{ regionName(data.region_id) }}</template>
      </Column>
      <Column field="farm_type" header="Loại" sortable style="width: 8rem">
        <template #body="{ data }">
          <Tag :value="farmTypeLabel(data.farm_type)" severity="info" rounded />
        </template>
      </Column>
      <Column field="ownership_type" header="Sở hữu" sortable style="width: 9rem">
        <template #body="{ data }">{{ ownershipLabel(data.ownership_type) }}</template>
      </Column>
      <Column field="capacity_headcount" header="Công suất" sortable style="width: 8rem">
        <template #body="{ data }">
          {{ data.capacity_headcount != null ? data.capacity_headcount.toLocaleString() : '—' }}
        </template>
      </Column>
      <Column field="baseline_risk_level" header="Mức rủi ro" sortable style="width: 9rem">
        <template #body="{ data }">
          <StatusBadge :value="data.baseline_risk_level" type="risk" />
        </template>
      </Column>
      <Column field="operational_status" header="Trạng thái" sortable style="width: 9rem">
        <template #body="{ data }">
          <StatusBadge :value="data.operational_status" type="status" />
        </template>
      </Column>
      <Column style="width: 4rem">
        <template #body="{ data }">
          <Button
            v-if="authStore.hasPermission('FARM_WRITE')"
            icon="pi pi-pencil"
            text
            rounded
            severity="secondary"
            @click.stop="openEdit(data)"
            v-tooltip.top="'Sửa'"
          />
        </template>
      </Column>

      <template #empty>
        <div class="empty-msg">Không có trại nào.</div>
      </template>
    </DataTable>

    <FarmFormDialog
      v-model:visible="showDialog"
      :farm="editFarm"
      :regions="farmStore.regions"
      @saved="onSaved"
    />
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.page-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.filter-bar {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-select {
  min-width: 10rem;
}

.farm-table :deep(.p-datatable-row-selected) {
  cursor: pointer;
}

.farm-table :deep(tr) {
  cursor: pointer;
}

.empty-msg {
  text-align: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
}
</style>
