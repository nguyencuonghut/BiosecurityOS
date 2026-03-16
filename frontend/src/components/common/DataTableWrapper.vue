<script setup>
/**
 * DataTableWrapper — Reusable PrimeVue DataTable with server-side pagination & search.
 *
 * Props:
 *   - value: Array of row data
 *   - totalRecords: Total count from server
 *   - loading: Boolean
 *   - rows: Page size (default 20)
 *   - globalFilterFields: Array of field names for search (optional)
 *
 * Events:
 *   - @page: { page, rows } — fired on page change
 *   - @sort: { sortField, sortOrder } — fired on sort
 *
 * Slots:
 *   - header: extra content in header area
 *   - default: DataColumn definitions
 */
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import { ref, watch } from 'vue'

const props = defineProps({
  value: { type: Array, default: () => [] },
  totalRecords: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  rows: { type: Number, default: 20 },
  globalFilterFields: { type: Array, default: () => [] },
  searchPlaceholder: { type: String, default: 'Tìm kiếm...' },
  showSearch: { type: Boolean, default: true },
})

const emit = defineEmits(['page', 'sort', 'search'])

const searchText = ref('')
let debounceTimer = null

function onPage(event) {
  emit('page', { page: event.page + 1, rows: event.rows })
}

function onSort(event) {
  const prefix = event.sortOrder === -1 ? '-' : ''
  emit('sort', { sortField: event.sortField, sortOrder: event.sortOrder, sort: prefix + event.sortField })
}

watch(searchText, (val) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => emit('search', val), 350)
})
</script>

<template>
  <DataTable
    :value="value"
    :totalRecords="totalRecords"
    :loading="loading"
    :rows="rows"
    :rowsPerPageOptions="[10, 20, 50]"
    paginator
    lazy
    stripedRows
    removableSort
    :globalFilterFields="globalFilterFields"
    @page="onPage"
    @sort="onSort"
    tableStyle="min-width: 50rem"
  >
    <template #header v-if="showSearch || $slots.header">
      <div class="dtw-header">
        <div class="dtw-header-left">
          <slot name="header" />
        </div>
        <div class="dtw-header-right" v-if="showSearch">
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText v-model="searchText" :placeholder="searchPlaceholder" />
          </IconField>
        </div>
      </div>
    </template>
    <slot />
  </DataTable>
</template>

<style scoped>
.dtw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.dtw-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.dtw-header-right {
  display: flex;
  align-items: center;
}
</style>
