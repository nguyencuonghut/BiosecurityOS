<script setup>
import { ref, onMounted, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import Drawer from 'primevue/drawer'
import Tag from 'primevue/tag'
import { useAuditLogStore } from '@/stores/auditLog.js'

const auditStore = useAuditLogStore()

const actionFilter = ref('')
const entityTypeFilter = ref(null)
const dateRange = ref(null)
const showDetail = ref(false)
const selectedLog = ref(null)

const entityTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Farm', value: 'farm' },
  { label: 'Assessment', value: 'assessment' },
  { label: 'Case', value: 'case' },
  { label: 'Task', value: 'task' },
  { label: 'Scar', value: 'scar' },
  { label: 'Lesson', value: 'lesson' },
  { label: 'User', value: 'user' },
  { label: 'Killer Event', value: 'killer_event' },
  { label: 'Notification', value: 'notification' },
  { label: 'Report', value: 'report' },
]

onMounted(() => auditStore.fetchLogs())

function applyFilters() {
  auditStore.filters.action = actionFilter.value || null
  auditStore.filters.entity_type = entityTypeFilter.value
  if (dateRange.value?.[0]) {
    auditStore.filters.date_from = dateRange.value[0].toISOString().slice(0, 10)
  } else {
    auditStore.filters.date_from = null
  }
  if (dateRange.value?.[1]) {
    auditStore.filters.date_to = dateRange.value[1].toISOString().slice(0, 10)
  } else {
    auditStore.filters.date_to = null
  }
  auditStore.filters.page = 1
  auditStore.fetchLogs()
}

function resetFilters() {
  actionFilter.value = ''
  entityTypeFilter.value = null
  dateRange.value = null
  auditStore.resetFilters()
  auditStore.fetchLogs()
}

function onPage(event) {
  auditStore.filters.page = event.page + 1
  auditStore.filters.page_size = event.rows
  auditStore.fetchLogs()
}

function openDetail(log) {
  selectedLog.value = log
  showDetail.value = true
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function prettyJson(obj) {
  if (!obj) return '—'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function summarizeChange(log) {
  if (!log.before_json && log.after_json) return 'Tạo mới'
  if (log.before_json && !log.after_json) return 'Xóa'
  if (log.before_json && log.after_json) return 'Cập nhật'
  return log.action || '—'
}
</script>

<template>
  <div class="audit-log-page">
    <div class="page-header">
      <h2>Nhật ký hệ thống</h2>
    </div>

    <DataTable
      :value="auditStore.logs"
      :totalRecords="auditStore.totalRecords"
      :loading="auditStore.loading"
      :rows="auditStore.filters.page_size"
      :rowsPerPageOptions="[10, 20, 50]"
      paginator
      lazy
      stripedRows
      @page="onPage"
    >
      <template #header>
        <div class="filter-bar">
          <Select
            v-model="entityTypeFilter"
            :options="entityTypeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Loại đối tượng"
            style="min-width: 10rem"
          />
          <InputText
            v-model="actionFilter"
            placeholder="Hành động..."
            style="min-width: 10rem"
            @keyup.enter="applyFilters"
          />
          <DatePicker
            v-model="dateRange"
            selectionMode="range"
            dateFormat="dd/mm/yy"
            placeholder="Khoảng thời gian"
            showIcon
            style="min-width: 14rem"
          />
          <Button label="Lọc" icon="pi pi-filter" @click="applyFilters" />
          <Button label="Xóa lọc" icon="pi pi-filter-slash" severity="secondary" text @click="resetFilters" />
        </div>
      </template>

      <Column header="Thời gian" style="width: 12rem">
        <template #body="{ data }">{{ formatDate(data.occurred_at) }}</template>
      </Column>
      <Column field="actor_user_id" header="Người thực hiện" style="width: 10rem">
        <template #body="{ data }">
          <span class="actor-id">{{ data.actor_user_id?.slice(0, 8) }}…</span>
        </template>
      </Column>
      <Column field="action" header="Hành động" style="min-width: 10rem" />
      <Column field="entity_type" header="Đối tượng" style="width: 8rem">
        <template #body="{ data }">
          <Tag :value="data.entity_type" severity="info" />
        </template>
      </Column>
      <Column header="Entity ID" style="width: 10rem">
        <template #body="{ data }">
          <span class="entity-id">{{ data.entity_id?.slice(0, 8) }}…</span>
        </template>
      </Column>
      <Column header="Tóm tắt" style="min-width: 10rem">
        <template #body="{ data }">{{ summarizeChange(data) }}</template>
      </Column>
      <Column style="width: 4rem">
        <template #body="{ data }">
          <Button icon="pi pi-eye" text rounded severity="secondary" v-tooltip.top="'Chi tiết'" @click="openDetail(data)" />
        </template>
      </Column>
      <template #empty>
        <div class="empty-msg">Không có bản ghi nhật ký nào.</div>
      </template>
    </DataTable>

    <!-- Detail Drawer -->
    <Drawer v-model:visible="showDetail" position="right" :style="{ width: '36rem' }" header="Chi tiết nhật ký">
      <template v-if="selectedLog">
        <div class="detail-section">
          <div class="detail-row">
            <label>Thời gian:</label>
            <span>{{ formatDate(selectedLog.occurred_at) }}</span>
          </div>
          <div class="detail-row">
            <label>Người thực hiện:</label>
            <span>{{ selectedLog.actor_user_id }}</span>
          </div>
          <div class="detail-row">
            <label>Hành động:</label>
            <Tag :value="selectedLog.action" severity="info" />
          </div>
          <div class="detail-row">
            <label>Đối tượng:</label>
            <span>{{ selectedLog.entity_type }} / {{ selectedLog.entity_id }}</span>
          </div>
          <div class="detail-row">
            <label>IP:</label>
            <span>{{ selectedLog.ip_address || '—' }}</span>
          </div>
          <div class="detail-row">
            <label>User Agent:</label>
            <span class="ua-text">{{ selectedLog.user_agent || '—' }}</span>
          </div>
        </div>

        <div class="json-diff">
          <div class="json-panel">
            <h4>Before</h4>
            <pre class="json-pre">{{ prettyJson(selectedLog.before_json) }}</pre>
          </div>
          <div class="json-panel">
            <h4>After</h4>
            <pre class="json-pre">{{ prettyJson(selectedLog.after_json) }}</pre>
          </div>
        </div>
      </template>
    </Drawer>
  </div>
</template>

<style scoped>
.audit-log-page { width: 100%; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.page-header h2 { margin: 0; font-size: 1.25rem; }
.filter-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; }
.actor-id, .entity-id { font-family: monospace; font-size: 0.8rem; }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }

.detail-section { margin-bottom: 1.5rem; }
.detail-row { display: flex; gap: 0.75rem; padding: 0.4rem 0; border-bottom: 1px solid var(--p-surface-border); }
.detail-row label { font-weight: 600; min-width: 9rem; font-size: 0.85rem; }
.detail-row span { font-size: 0.85rem; word-break: break-all; }
.ua-text { font-size: 0.75rem; color: var(--p-text-muted-color); }

.json-diff { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.json-panel h4 { margin: 0 0 0.5rem; font-size: 0.9rem; }
.json-pre {
  background: var(--p-surface-ground);
  border: 1px solid var(--p-surface-border);
  border-radius: 6px;
  padding: 0.75rem;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 24rem;
}

@media screen and (max-width: 768px) {
  .json-diff { grid-template-columns: 1fr; }
}
</style>
