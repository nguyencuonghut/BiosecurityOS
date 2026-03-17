<script setup>
import { ref } from 'vue'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'

// Mock farm benchmarking data
const benchmarkData = ref([
  {
    id: 1,
    rank: 1,
    name: 'Trại nái Bắc Ninh',
    code: 'F003',
    score: 85.2,
    trend: 2.3,
    status: 'strong',
    category: 'nái'
  },
  {
    id: 2,
    rank: 2,
    name: 'Trại nái Hải Dương',
    code: 'F001',
    score: 82.4,
    trend: 1.5,
    status: 'good',
    category: 'nái'
  },
  {
    id: 3,
    rank: 3,
    name: 'Trại thịt Nam Đình',
    code: 'F005',
    score: 76.8,
    trend: -0.5,
    status: 'fair',
    category: 'thịt'
  },
  {
    id: 4,
    rank: 4,
    name: 'Trại nái Hà Nam',
    code: 'F006',
    score: 74.5,
    trend: -2.1,
    status: 'warning',
    category: 'nái'
  },
  {
    id: 5,
    rank: 5,
    name: 'Trại thịt Thanh Hóa',
    code: 'F002',
    score: 68.3,
    trend: -3.2,
    status: 'critical',
    category: 'thịt'
  }
])

const getSeverityByStatus = (status) => {
  const map = {
    'strong': 'success',
    'good': 'info',
    'fair': 'warning',
    'warning': 'warning',
    'critical': 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = {
    'strong': 'Tốt lắm',
    'good': 'Tốt',
    'fair': 'Trung bình',
    'warning': 'Cảnh báo',
    'critical': 'Nguy hiểm'
  }
  return map[status] || status
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
        :value="benchmarkData"
        class="benchmark-table"
        responsive-layout="scroll"
        table-style="min-width: 100%"
        :rows="10"
        striped-rows
      >
        <!-- Rank Column -->
        <Column field="rank" header="Xếp hạng" style="width: 8%" class="text-center">
          <template #body="slotProps">
            <div class="rank-badge" :class="`rank-${slotProps.data.rank}`">
              {{ slotProps.data.rank }}
            </div>
          </template>
        </Column>

        <!-- Farm Column -->
        <Column field="name" header="Trại" style="width: 30%">
          <template #body="slotProps">
            <div class="farm-column">
              <strong>{{ slotProps.data.name }}</strong>
              <p class="farm-code">{{ slotProps.data.code }}</p>
            </div>
          </template>
        </Column>

        <!-- Score Column -->
        <Column field="score" header="Điểm" style="width: 25%">
          <template #body="slotProps">
            <div class="score-column">
              <div class="score-value">{{ slotProps.data.score }}/100</div>
              <ProgressBar
                :value="slotProps.data.score"
                class="score-bar"
                :show-value="false"
              />
            </div>
          </template>
        </Column>

        <!-- Trend Column -->
        <Column field="trend" header="Xu hướng" style="width: 15%">
          <template #body="slotProps">
            <div class="trend-column">
              <i
                :class="`pi ${slotProps.data.trend > 0 ? 'pi-arrow-up text-green-500' : 'pi-arrow-down text-red-500'}`"
              ></i>
              <span :class="slotProps.data.trend > 0 ? 'text-green-500' : 'text-red-500'">
                {{ slotProps.data.trend > 0 ? '+' : '' }}{{ slotProps.data.trend }}%
              </span>
            </div>
          </template>
        </Column>

        <!-- Status Column -->
        <Column field="status" header="Trạng thái" style="width: 20%">
          <template #body="slotProps">
            <Tag
              :value="getStatusLabel(slotProps.data.status)"
              :severity="getSeverityByStatus(slotProps.data.status)"
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
.rank-5 {
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
