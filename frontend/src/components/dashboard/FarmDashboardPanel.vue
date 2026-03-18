<script setup>
import { ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'
import { getFarmDashboard } from '@/services/dashboardService.js'

use([LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const props = defineProps({
  farmId: { type: String, required: true },
})

const loading = ref(false)
const error = ref(null)
const data = ref(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    data.value = await getFarmDashboard(props.farmId)
  } catch (err) {
    error.value = err.message || 'Không thể tải dữ liệu dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
watch(() => props.farmId, loadData)

function buildScoreChartOption(scores) {
  if (!scores || !scores.length) return {}
  const dates = scores.map((s) => s.date)
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: 'Điểm', min: 0, max: 100 },
    series: [
      { name: 'Tổng', type: 'line', data: scores.map((s) => s.overall_score), smooth: true, itemStyle: { color: '#3B82F6' } },
      { name: 'Hạ tầng', type: 'line', data: scores.map((s) => s.hardware_score), smooth: true, itemStyle: { color: '#10B981' } },
      { name: 'Quy trình', type: 'line', data: scores.map((s) => s.process_score), smooth: true, itemStyle: { color: '#F59E0B' } },
      { name: 'Hành vi', type: 'line', data: scores.map((s) => s.behavior_score), smooth: true, itemStyle: { color: '#8B5CF6' } },
      { name: 'Giám sát', type: 'line', data: scores.map((s) => s.monitoring_score), smooth: true, itemStyle: { color: '#EC4899' } },
    ],
  }
}

function buildTrustChartOption(trend) {
  if (!trend || !trend.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: trend.map((t) => t.date) },
    yAxis: { type: 'value', name: 'Điểm', min: 0, max: 100 },
    series: [
      { name: 'Trust Score', type: 'line', data: trend.map((t) => t.trust_score), smooth: true, areaStyle: { opacity: 0.2 }, itemStyle: { color: '#3B82F6' } },
      { name: 'Gap Score', type: 'line', data: trend.map((t) => t.gap_score), smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#EF4444' } },
    ],
  }
}

function kpiSeverity(val, thresholdLow = 1) {
  return val > thresholdLow ? 'danger' : 'success'
}
</script>

<template>
  <div class="farm-dashboard-panel">
    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <template v-if="data">
      <!-- KPI Summary Row -->
      <div class="kpi-row">
        <Card class="kpi-card">
          <template #content>
            <div class="kpi-item">
              <i class="pi pi-folder-open kpi-icon"></i>
              <div>
                <div class="kpi-value">{{ data.open_cases }}</div>
                <div class="kpi-label">Case mở</div>
              </div>
            </div>
          </template>
        </Card>
        <Card class="kpi-card">
          <template #content>
            <div class="kpi-item">
              <i class="pi pi-list kpi-icon"></i>
              <div>
                <div class="kpi-value">{{ data.open_tasks }}</div>
                <div class="kpi-label">Task mở</div>
              </div>
            </div>
          </template>
        </Card>
        <Card class="kpi-card">
          <template #content>
            <div class="kpi-item">
              <i class="pi pi-clock kpi-icon" :class="{ 'text-red': data.overdue_tasks > 0 }"></i>
              <div>
                <Tag :value="String(data.overdue_tasks)" :severity="kpiSeverity(data.overdue_tasks)" />
                <div class="kpi-label">Quá hạn</div>
              </div>
            </div>
          </template>
        </Card>
        <Card class="kpi-card">
          <template #content>
            <div class="kpi-item">
              <i class="pi pi-map-marker kpi-icon"></i>
              <div>
                <div class="kpi-value">{{ data.active_scars }}</div>
                <div class="kpi-label">Scar đang mở</div>
              </div>
            </div>
          </template>
        </Card>
        <Card class="kpi-card">
          <template #content>
            <div class="kpi-item">
              <i class="pi pi-heart-fill kpi-icon"></i>
              <div>
                <Tag :value="String(data.killer_metric_open)" :severity="kpiSeverity(data.killer_metric_open)" />
                <div class="kpi-label">Killer Metric</div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Score Over Time Chart -->
      <Card class="chart-card">
        <template #title>
          <i class="pi pi-chart-line"></i>
          Xu hướng điểm ATSH
        </template>
        <template #content>
          <div v-if="data.scores_over_time.length">
            <VChart :option="buildScoreChartOption(data.scores_over_time)" autoresize style="height: 320px" />
          </div>
          <div v-else class="empty-state">Chưa có dữ liệu đánh giá</div>
        </template>
      </Card>

      <!-- Trust Trend Chart -->
      <Card class="chart-card">
        <template #title>
          <i class="pi pi-shield"></i>
          Xu hướng Trust Score
        </template>
        <template #content>
          <div v-if="data.trust_trend.length">
            <VChart :option="buildTrustChartOption(data.trust_trend)" autoresize style="height: 280px" />
          </div>
          <div v-else class="empty-state">Chưa có dữ liệu trust score</div>
        </template>
      </Card>
    </template>
  </div>
</template>

<style scoped>
.farm-dashboard-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 3rem;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.kpi-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.kpi-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.kpi-icon {
  font-size: 1.5rem;
  color: var(--p-primary-color);
}

.kpi-icon.text-red {
  color: var(--p-red-500);
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.kpi-label {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  margin-top: 0.25rem;
}

.chart-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
  font-style: italic;
}

@media screen and (max-width: 600px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
