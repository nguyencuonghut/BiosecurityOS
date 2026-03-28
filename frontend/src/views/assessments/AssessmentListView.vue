<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment.js'
import { useFarmStore } from '@/stores/farm.js'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useToast } from 'primevue/usetoast'
import * as scorecardService from '@/services/scorecardService.js'

const router = useRouter()
const store = useAssessmentStore()
const farmStore = useFarmStore()
const toast = useToast()

const showCreateDialog = ref(false)
const activeTemplates = ref([])
const createForm = ref({ farm_id: null, template_id: null, assessment_type: null })

const typeOptions = [
  { label: 'Tự đánh giá',       value: 'self' },
  { label: 'Đánh giá định kỳ', value: 'scheduled_audit' },
  { label: 'Đánh giá đột xuất', value: 'spot' },
  { label: 'Đánh giá ẩn danh',   value: 'blind' },
  { label: 'Đánh giá sau sự cố', value: 'incident_review' },
]

const statusOptions = [
  { label: 'Nháp',        value: 'draft' },
  { label: 'Đã gửi',      value: 'submitted' },
  { label: 'Đã duyệt',    value: 'reviewed' },
  { label: 'Đã khóa',     value: 'locked' },
]

onMounted(async () => {
  store.fetchAssessments()
  await farmStore.fetchFarms()
})

function onPage(event) {
  store.filters.page = event.page + 1
  store.filters.page_size = event.rows
  store.fetchAssessments()
}

function onFilterChange() {
  store.filters.page = 1
  store.fetchAssessments()
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('vi-VN')
}

function formatScore(s) {
  if (s == null) return '—'
  return Number(s).toFixed(0)
}

function scoreClass(s) {
  if (s == null) return ''
  const n = Number(s)
  if (n >= 80) return 'score-good'
  if (n >= 60) return 'score-warn'
  return 'score-bad'
}

async function openCreateDialog() {
  try {
    const result = await scorecardService.listTemplates({ status: 'active', page_size: 100 })
    activeTemplates.value = result.data
  } catch {
    activeTemplates.value = []
  }
  createForm.value = { farm_id: null, template_id: null, assessment_type: null }
  showCreateDialog.value = true
}

async function handleCreate() {
  try {
    const created = await store.createAssessment(createForm.value)
    showCreateDialog.value = false
    toast.add({ severity: 'success', summary: 'Đã tạo đánh giá', life: 3000 })
    router.push(`/assessments/${created.id}`)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Không thể tạo', life: 5000 })
  }
}

function openDetail(row) {
  router.push(`/assessments/${row.id}`)
}
</script>

<template>
  <div class="assessment-list">
    <div class="page-header">
      <h2>Danh sách Đánh giá</h2>
      <Button label="Tạo đánh giá" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <div class="filter-bar">
      <Select
        v-model="store.filters.farm_id"
        :options="farmStore.farms"
        optionLabel="name"
        optionValue="id"
        placeholder="Trại"
        showClear
        filter
        @change="onFilterChange"
      />
      <Select
        v-model="store.filters.assessment_type"
        :options="typeOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Loại đánh giá"
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
      :value="store.assessments"
      :loading="store.loading"
      :totalRecords="store.totalRecords"
      :rows="store.filters.page_size"
      :lazy="true"
      paginator
      @page="onPage"
      stripedRows
      class="mt-3"
    >
      <Column header="Ngày" style="width: 10%">
        <template #body="{ data }">{{ formatDate(data.assessment_date) }}</template>
      </Column>
      <Column header="Trại" style="width: 14%">
        <template #body="{ data }">{{ data.farm_name || '—' }}</template>
      </Column>
      <Column field="assessment_type" header="Loại" style="width: 12%">
        <template #body="{ data }">{{ data.assessment_type_label }}</template>
      </Column>
      <Column field="performed_by_name_snapshot" header="Người đánh giá" style="width: 16%" />
      <Column header="Điểm tổng" style="width: 8%">
        <template #body="{ data }">
          <span :class="scoreClass(data.overall_score)" class="score-value">{{ formatScore(data.overall_score) }}</span>
        </template>
      </Column>
      <Column header="HW" style="width: 6%">
        <template #body="{ data }">
          <span :class="scoreClass(data.hardware_score)" class="score-sm">{{ formatScore(data.hardware_score) }}</span>
        </template>
      </Column>
      <Column header="SW" style="width: 6%">
        <template #body="{ data }">
          <span :class="scoreClass(data.process_score)" class="score-sm">{{ formatScore(data.process_score) }}</span>
        </template>
      </Column>
      <Column header="BH" style="width: 6%">
        <template #body="{ data }">
          <span :class="scoreClass(data.behavior_score)" class="score-sm">{{ formatScore(data.behavior_score) }}</span>
        </template>
      </Column>
      <Column header="MN" style="width: 6%">
        <template #body="{ data }">
          <span :class="scoreClass(data.monitoring_score)" class="score-sm">{{ formatScore(data.monitoring_score) }}</span>
        </template>
      </Column>
      <Column field="status" header="Trạng thái" style="width: 10%">
        <template #body="{ data }">
          <StatusBadge :value="data.status" :label="data.status_label" />
        </template>
      </Column>
      <Column header="" style="width: 8%">
        <template #body="{ data }">
          <Button icon="pi pi-eye" text rounded size="small" @click="openDetail(data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateDialog" header="Tạo đánh giá mới" :modal="true" style="width: 30rem">
      <div class="dialog-form">
        <div class="field">
          <label>Trại *</label>
          <Select
            v-model="createForm.farm_id"
            :options="farmStore.farms"
            optionLabel="name"
            optionValue="id"
            placeholder="Chọn trại"
            filter
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Template *</label>
          <Select
            v-model="createForm.template_id"
            :options="activeTemplates"
            optionLabel="name"
            optionValue="id"
            placeholder="Chọn template"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Loại đánh giá *</label>
          <Select
            v-model="createForm.assessment_type"
            :options="typeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Chọn loại"
            class="w-full"
          />
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
.dialog-form {
  display: flex;
  flex-direction: column;
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
.score-value {
  font-weight: 700;
  font-size: 1rem;
}
.score-sm {
  font-weight: 600;
  font-size: 0.85rem;
}
.score-good { color: var(--p-green-500); }
.score-warn { color: var(--p-orange-500); }
.score-bad { color: var(--p-red-500); }
.mt-3 { margin-top: 0.75rem; }
</style>
