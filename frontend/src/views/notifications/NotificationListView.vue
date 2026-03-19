<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useNotificationStore } from '@/stores/notification.js'

const router = useRouter()
const toast = useToast()
const notifStore = useNotificationStore()

const statusFilter = ref(null)
const selected = ref([])

const statusOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Chưa đọc', value: 'queued' },
  { label: 'Đã đọc', value: 'read' },
]

onMounted(() => {
  notifStore.filters.page = 1
  notifStore.filters.page_size = 20
  notifStore.fetchNotifications()
})

watch(statusFilter, (val) => {
  notifStore.filters.status = val
  notifStore.filters.page = 1
  notifStore.fetchNotifications()
})

function onPage(event) {
  notifStore.filters.page = event.page + 1
  notifStore.filters.page_size = event.rows
  notifStore.fetchNotifications()
}

function statusSeverity(n) {
  return n.read_at ? 'secondary' : 'info'
}

function statusLabel(n) {
  return n.read_at ? 'Đã đọc' : 'Chưa đọc'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function onMarkRead(notif) {
  if (notif.read_at) return
  await notifStore.markAsRead(notif.id)
  toast.add({ severity: 'success', summary: 'Đã đánh dấu đã đọc', life: 2000 })
}

async function onBulkMarkRead() {
  const unreadIds = selected.value.filter((n) => !n.read_at).map((n) => n.id)
  if (!unreadIds.length) return
  const count = await notifStore.bulkMarkAsRead(unreadIds)
  selected.value = []
  toast.add({ severity: 'success', summary: `Đã đánh dấu ${count} thông báo đã đọc`, life: 2000 })
}

function onRowClick(notif) {
  if (notif.entity_type && notif.entity_id) {
    const routeMap = { case: 'CaseDetail', task: 'TaskDetail', farm: 'FarmDetail' }
    const name = routeMap[notif.entity_type]
    if (name) router.push({ name, params: { id: notif.entity_id } })
  }
}
</script>

<template>
  <div class="notif-list-page">
    <div class="page-header">
      <h2>Thông báo</h2>
      <Button
        label="Đánh dấu đã đọc"
        icon="pi pi-check"
        severity="secondary"
        :disabled="!selected.filter((n) => !n.read_at).length"
        @click="onBulkMarkRead"
      />
    </div>

    <DataTable
      v-model:selection="selected"
      :value="notifStore.notifications"
      :totalRecords="notifStore.totalRecords"
      :loading="notifStore.loading"
      :rows="notifStore.filters.page_size"
      :rowsPerPageOptions="[10, 20, 50]"
      paginator
      lazy
      stripedRows
      dataKey="id"
      @page="onPage"
      @row-click="({ data }) => onRowClick(data)"
      selectionMode="multiple"
    >
      <template #header>
        <div class="filter-bar">
          <Select
            v-model="statusFilter"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Trạng thái"
            style="min-width: 10rem"
          />
        </div>
      </template>

      <Column selectionMode="multiple" headerStyle="width: 3rem" />
      <Column field="title" header="Tiêu đề" style="min-width: 14rem">
        <template #body="{ data }">
          <span :class="{ 'fw-bold': !data.read_at }">{{ data.title }}</span>
        </template>
      </Column>
      <Column field="body" header="Nội dung" style="min-width: 16rem">
        <template #body="{ data }">
          <span class="notif-body-cell">{{ data.body }}</span>
        </template>
      </Column>
      <Column header="Loại" style="width: 7rem">
        <template #body="{ data }">
          <Tag v-if="data.entity_type" :value="data.entity_type" severity="info" />
          <span v-else class="text-muted">—</span>
        </template>
      </Column>
      <Column header="Trạng thái" style="width: 7rem">
        <template #body="{ data }">
          <Tag :value="statusLabel(data)" :severity="statusSeverity(data)" />
        </template>
      </Column>
      <Column header="Thời gian" sortable style="width: 11rem">
        <template #body="{ data }">{{ formatDate(data.sent_at || data.created_at) }}</template>
      </Column>
      <Column style="width: 5rem">
        <template #body="{ data }">
          <Button
            v-if="!data.read_at"
            icon="pi pi-eye"
            text
            rounded
            severity="secondary"
            v-tooltip.top="'Đánh dấu đã đọc'"
            @click.stop="onMarkRead(data)"
          />
        </template>
      </Column>
      <template #empty>
        <div class="empty-msg">Không có thông báo nào.</div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.notif-list-page { width: 100%; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.page-header h2 { margin: 0; font-size: 1.25rem; }
.filter-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.fw-bold { font-weight: 600; }
.notif-body-cell { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; font-size: 0.85rem; color: var(--p-text-muted-color); }
.text-muted { color: var(--p-text-muted-color); }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }
</style>
