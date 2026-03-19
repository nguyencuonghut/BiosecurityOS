<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import { useReportStore } from '@/stores/report.js'
import { useFarmStore } from '@/stores/farm.js'

const toast = useToast()
const reportStore = useReportStore()
const farmStore = useFarmStore()

onMounted(() => {
  reportStore.fetchReports()
})

const reportType = ref(null)
const format = ref('xlsx')
const regionId = ref(null)
const farmId = ref(null)
const dateRange = ref(null)

const reportTypeOptions = [
  { label: 'Tổng hợp ATSH tháng', value: 'monthly_biosecurity_summary' },
  { label: 'So sánh điểm trại', value: 'farm_score_comparison' },
  { label: 'Backlog hồ sơ', value: 'case_backlog' },
  { label: 'Tasks quá hạn', value: 'overdue_tasks' },
  { label: 'Tổng hợp Killer Metrics', value: 'killer_metrics_summary' },
  { label: 'Báo cáo Trust Gap', value: 'trust_gap_report' },
  { label: 'Scar Hotspot', value: 'scar_hotspot_report' },
]

const formatOptions = [
  { label: 'Excel (.xlsx)', value: 'xlsx' },
  { label: 'CSV (.csv)', value: 'csv' },
  { label: 'PDF (.pdf)', value: 'pdf' },
]

const canGenerate = computed(() => !!reportType.value)

const regionOptions = computed(() =>
  (farmStore.regions || []).map((r) => ({ label: r.name, value: r.id })),
)

const farmOptions = computed(() => {
  let list = farmStore.farms || []
  if (regionId.value) list = list.filter((f) => f.region_id === regionId.value)
  return list.map((f) => ({ label: `${f.farm_code} - ${f.name}`, value: f.id }))
})

farmStore.fetchRegions()
farmStore.filters.page_size = 100
farmStore.fetchFarms()

function statusSeverity(status) {
  const map = { completed: 'success', pending: 'warn', processing: 'info', failed: 'danger' }
  return map[status] || 'secondary'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function onGenerate() {
  if (!reportType.value) return
  const filters = {}
  if (regionId.value) filters.region_id = regionId.value
  if (farmId.value) filters.farm_id = farmId.value
  if (dateRange.value?.[0]) {
    filters.date_from = dateRange.value[0].toISOString().slice(0, 10)
  }
  if (dateRange.value?.[1]) {
    filters.date_to = dateRange.value[1].toISOString().slice(0, 10)
  }

  try {
    const report = await reportStore.generateReport({
      report_type: reportType.value,
      format: format.value,
      filters: Object.keys(filters).length ? filters : null,
    })
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Báo cáo "${reportLabel(report.report_type)}" đã tạo xong.`, life: 4000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.error?.message || 'Không thể tạo báo cáo.', life: 5000 })
  }
}

async function onDownload(report) {
  try {
    await reportStore.downloadReport(report.id)
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải báo cáo.', life: 4000 })
  }
}

async function onView(report) {
  try {
    await reportStore.viewReportPdf(report.id)
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể mở báo cáo.', life: 4000 })
  }
}

function reportLabel(type) {
  return reportTypeOptions.find((o) => o.value === type)?.label || type
}
</script>

<template>
  <div class="report-page">
    <div class="page-header">
      <h2>Báo cáo</h2>
    </div>

    <Card class="generate-card">
      <template #title>Tạo báo cáo mới</template>
      <template #content>
        <div class="form-grid">
          <div class="field">
            <label>Loại báo cáo <span class="required">*</span></label>
            <Select
              v-model="reportType"
              :options="reportTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Chọn loại báo cáo"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>Định dạng</label>
            <Select
              v-model="format"
              :options="formatOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>Vùng</label>
            <Select
              v-model="regionId"
              :options="regionOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tất cả vùng"
              showClear
              class="w-full"
            />
          </div>
          <div class="field">
            <label>Trại</label>
            <Select
              v-model="farmId"
              :options="farmOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tất cả trại"
              showClear
              filter
              class="w-full"
            />
          </div>
          <div class="field span-2">
            <label>Khoảng thời gian</label>
            <DatePicker
              v-model="dateRange"
              selectionMode="range"
              dateFormat="dd/mm/yy"
              placeholder="Chọn khoảng thời gian"
              showIcon
              class="w-full"
            />
          </div>
        </div>
        <div class="actions">
          <Button
            label="Tạo báo cáo"
            icon="pi pi-file-export"
            :loading="reportStore.generating"
            :disabled="!canGenerate"
            @click="onGenerate"
          />
        </div>
      </template>
    </Card>

    <Card class="history-card">
      <template #title>Lịch sử báo cáo</template>
      <template #content>
        <DataTable
          :value="reportStore.reports"
          stripedRows
          :rows="10"
        >
          <Column header="Loại báo cáo" style="min-width: 14rem">
            <template #body="{ data }">{{ reportLabel(data.report_type) }}</template>
          </Column>
          <Column field="format" header="Định dạng" style="width: 7rem">
            <template #body="{ data }">
              <Tag :value="data.format.toUpperCase()" severity="info" />
            </template>
          </Column>
          <Column field="status" header="Trạng thái" style="width: 8rem">
            <template #body="{ data }">
              <Tag :value="data.status" :severity="statusSeverity(data.status)" />
            </template>
          </Column>
          <Column header="Ngày tạo" style="width: 11rem">
            <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
          </Column>
          <Column header="Thao tác" style="width: 9rem">
            <template #body="{ data }">
              <template v-if="data.status === 'completed'">
                <Button
                  v-if="data.format === 'pdf'"
                  icon="pi pi-eye"
                  text
                  rounded
                  severity="info"
                  v-tooltip.top="'Xem'"
                  @click="onView(data)"
                />
                <Button
                  icon="pi pi-download"
                  text
                  rounded
                  severity="success"
                  v-tooltip.top="'Tải xuống'"
                  @click="onDownload(data)"
                />
              </template>
              <i v-else-if="data.status === 'failed'" class="pi pi-times-circle" style="color: var(--p-red-500)" v-tooltip.top="data.error_message" />
            </template>
          </Column>
          <template #empty>
            <div class="empty-msg">Chưa có báo cáo nào. Hãy tạo báo cáo mới.</div>
          </template>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.report-page { width: 100%; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.page-header h2 { margin: 0; font-size: 1.25rem; }
.generate-card { margin-bottom: 1.5rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-weight: 600; font-size: 0.85rem; }
.required { color: var(--p-red-500); }
.span-2 { grid-column: span 2; }
.actions { margin-top: 1.25rem; display: flex; justify-content: flex-end; }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }
.w-full { width: 100%; }
@media screen and (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: span 1; }
}
</style>
