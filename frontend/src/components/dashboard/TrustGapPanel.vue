<script setup>
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'

defineProps({
  data: { type: Array, default: () => [] },
})

function trustSeverity(score) {
  if (score == null) return 'secondary'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warn'
  return 'danger'
}

function trustLabel(score) {
  if (score == null) return '—'
  if (score >= 80) return 'Cao'
  if (score >= 60) return 'Trung bình'
  return 'Thấp'
}
</script>

<template>
  <Card class="trust-gap-card">
    <template #title>
      <i class="pi pi-shield"></i>
      Trust Gap – Khoảng cách tin cậy
    </template>

    <template #content>
      <DataTable
        :value="data"
        class="trust-gap-table"
        responsive-layout="scroll"
        :rows="10"
        striped-rows
        sort-field="trust_score"
        :sort-order="1"
      >
        <Column field="farm_name" header="Trại" style="width: 30%">
          <template #body="{ data: row }">
            <div>
              <strong>{{ row.farm_name }}</strong>
              <p class="farm-meta">{{ row.farm_code }} · {{ row.farm_type }} · {{ row.region_name }}</p>
            </div>
          </template>
        </Column>

        <Column field="trust_score" header="Điểm tin cậy" style="width: 20%" sortable>
          <template #body="{ data: row }">
            <Tag
              :value="row.trust_score != null ? row.trust_score.toFixed(1) : '—'"
              :severity="trustSeverity(row.trust_score)"
            />
          </template>
        </Column>

        <Column field="gap_score" header="Khoảng cách" style="width: 20%" sortable>
          <template #body="{ data: row }">
            <span class="gap-value" :class="{ 'gap-high': row.gap_score > 20 }">
              {{ row.gap_score != null ? row.gap_score.toFixed(1) : '—' }}
            </span>
          </template>
        </Column>

        <Column field="is_low_trust" header="Mức tin cậy" style="width: 15%">
          <template #body="{ data: row }">
            <Tag
              :value="trustLabel(row.trust_score)"
              :severity="trustSeverity(row.trust_score)"
            />
          </template>
        </Column>

        <Column field="snapshot_date" header="Cập nhật" style="width: 15%">
          <template #body="{ data: row }">
            {{ row.snapshot_date ? new Date(row.snapshot_date).toLocaleDateString('vi-VN') : '—' }}
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>

<style scoped>
.trust-gap-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.farm-meta {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.gap-value {
  font-weight: 600;
}

.gap-high {
  color: var(--p-red-500);
}
</style>
