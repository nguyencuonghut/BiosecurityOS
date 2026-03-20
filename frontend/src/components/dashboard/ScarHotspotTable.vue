<script setup>
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

defineProps({
  data: { type: Array, default: () => [] },
})

function scarSeverity(count) {
  if (count >= 5) return 'danger'
  if (count >= 3) return 'warn'
  return 'info'
}
</script>

<template>
  <Card class="scar-hotspot-card">
    <template #title>
      <i class="pi pi-map-marker"></i>
      Scar Hotspot – Điểm nóng vi phạm lặp
    </template>

    <template #content>
      <DataTable
        :value="data"
        class="scar-table"
        responsive-layout="scroll"
        :rows="10"
        striped-rows
        sort-field="scar_count"
        :sort-order="-1"
      >
        <Column field="farm_name" header="Trại" style="width: 30%">
          <template #body="{ data: row }">
            <div>
              <strong>{{ row.farm_name }}</strong>
              <p class="farm-meta">{{ row.farm_code }}</p>
            </div>
          </template>
        </Column>

        <Column field="scar_type" header="Loại Scar" style="width: 20%">
          <template #body="{ data: row }">
            <Tag :value="row.scar_type_label || row.scar_type" severity="secondary" />
          </template>
        </Column>

        <Column field="scar_count" header="Số vi phạm" style="width: 15%" sortable>
          <template #body="{ data: row }">
            <Tag :value="String(row.scar_count)" :severity="scarSeverity(row.scar_count)" />
          </template>
        </Column>

        <Column field="recurring_count" header="Lặp lại" style="width: 15%" sortable>
          <template #body="{ data: row }">
            <span class="recurring" :class="{ 'recurring-high': row.recurring_count > 0 }">
              {{ row.recurring_count }}
            </span>
          </template>
        </Column>

        <Column field="total_recurrence" header="Tổng tái phạm" style="width: 20%" sortable>
          <template #body="{ data: row }">
            <span class="recurrence-total">{{ row.total_recurrence }}</span>
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>

<style scoped>
.scar-hotspot-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.farm-meta {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.recurring {
  font-weight: 600;
}

.recurring-high {
  color: var(--p-red-500);
}

.recurrence-total {
  font-weight: 600;
  color: var(--p-text-color);
}
</style>
