<script setup>
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const router = useRouter()

function scoreSeverity(score) {
  if (score == null) return 'secondary'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warn'
  return 'danger'
}

function navigateToFarm(farmId) {
  router.push({ name: 'FarmDetail', params: { id: farmId } })
}
</script>

<template>
  <Card class="benchmark-card">
    <template #title>
      <i class="pi pi-chart-line"></i>
      Bảng xếp hạng trại
    </template>

    <template #content>
      <DataTable
        :value="data"
        class="benchmark-table"
        responsive-layout="scroll"
        table-style="min-width: 100%"
        :rows="10"
        striped-rows
        @row-click="(e) => navigateToFarm(e.data.farm_id)"
        row-hover
      >
        <!-- Rank Column -->
        <Column field="rank" header="Hạng" style="width: 8%" class="text-center">
          <template #body="slotProps">
            <div class="rank-badge" :class="`rank-${slotProps.data.rank <= 3 ? slotProps.data.rank : 'default'}`">
              {{ slotProps.data.rank }}
            </div>
          </template>
        </Column>

        <!-- Farm Column -->
        <Column field="farm_name" header="Trại" style="width: 30%">
          <template #body="slotProps">
            <div class="farm-column">
              <strong>{{ slotProps.data.farm_name }}</strong>
              <p class="farm-code">{{ slotProps.data.farm_code }} · {{ slotProps.data.farm_type }} · {{ slotProps.data.region_name }}</p>
            </div>
          </template>
        </Column>

        <!-- Score Column -->
        <Column field="overall_score" header="Điểm ATSH" style="width: 25%" sortable>
          <template #body="slotProps">
            <div class="score-column">
              <div class="score-value">{{ slotProps.data.overall_score != null ? slotProps.data.overall_score.toFixed(1) : '—' }}/100</div>
              <ProgressBar
                :value="slotProps.data.overall_score ?? 0"
                class="score-bar"
                :show-value="false"
              />
            </div>
          </template>
        </Column>

        <!-- Percentile Column -->
        <Column field="percentile" header="Phân vị" style="width: 15%" sortable>
          <template #body="slotProps">
            <Tag
              :value="`Top ${slotProps.data.percentile != null ? slotProps.data.percentile.toFixed(0) : '—'}%`"
              :severity="scoreSeverity(slotProps.data.percentile)"
            />
          </template>
        </Column>

        <!-- Status Column -->
        <Column field="overall_score" header="Trạng thái" style="width: 20%">
          <template #body="slotProps">
            <Tag
              :value="slotProps.data.overall_score >= 80 ? 'Tốt' : slotProps.data.overall_score >= 60 ? 'Trung bình' : 'Cần cải thiện'"
              :severity="scoreSeverity(slotProps.data.overall_score)"
            />
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>

<style scoped>
.benchmark-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.benchmark-table {
  width: 100%;
}

.rank-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.875rem;
  color: white;
  margin: 0 auto;
}

.rank-1 {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #333;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.rank-2 {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #333;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
}

.rank-3 {
  background: linear-gradient(135deg, #cd7f32, #d4a574);
  color: white;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.3);
}

.rank-4,
.rank-5,
.rank-default {
  background: var(--p-surface-border);
  color: var(--p-text-color);
}

.farm-column {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.farm-code {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  font-weight: 500;
}

.score-column {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.score-value {
  font-weight: 600;
  font-size: 1rem;
  color: var(--p-text-color);
}

.score-bar {
  height: 8px;
  max-width: 150px;
}

.trend-column {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

/* Responsive */
@media screen and (max-width: 768px) {
  .rank-badge {
    width: 28px;
    height: 28px;
    font-size: 0.75rem;
  }

  .farm-code {
    font-size: 0.65rem;
  }
}
</style>
