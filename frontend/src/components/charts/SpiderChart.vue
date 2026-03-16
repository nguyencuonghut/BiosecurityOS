<script setup>
import { computed, ref, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([RadarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  data: { type: Object, required: true },
  comparison: { type: Object, default: null },
  overallScore: { type: Number, default: null },
})

const option = computed(() => {
  const axes = props.data.axes || []
  const indicator = axes.map((a) => ({ name: a.label, max: 100 }))
  const values = axes.map((a) => a.score ?? 0)

  const series = [
    {
      name: 'Điểm đánh giá',
      type: 'radar',
      data: [
        {
          value: values,
          name: 'Đánh giá hiện tại',
          areaStyle: { opacity: 0.25 },
          lineStyle: { width: 2 },
          itemStyle: { color: '#3B82F6' },
        },
      ],
    },
  ]

  // Add comparison overlay if provided
  if (props.comparison?.axes) {
    const compValues = props.comparison.axes.map((a) => a.score ?? 0)
    series[0].data.push({
      value: compValues,
      name: 'So sánh',
      areaStyle: { opacity: 0.15 },
      lineStyle: { width: 2, type: 'dashed' },
      itemStyle: { color: '#F59E0B' },
    })
  }

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const vals = params.value
        return axes.map((a, i) => `${a.label}: <strong>${vals[i]}</strong>`).join('<br/>')
      },
    },
    legend: props.comparison ? { data: ['Đánh giá hiện tại', 'So sánh'], bottom: 0 } : undefined,
    radar: {
      indicator,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#666',
        fontSize: 13,
        fontWeight: 600,
      },
      splitArea: {
        areaStyle: { color: ['#fff', '#f8f9fa', '#fff', '#f8f9fa', '#fff'] },
      },
    },
    series,
  }
})
</script>

<template>
  <div class="spider-chart-wrapper">
    <div class="chart-container">
      <VChart :option="option" autoresize style="height: 340px; min-width: 340px" />
    </div>
    <div class="score-summary">
      <div v-if="overallScore != null" class="score-item overall-row">
        <span class="score-label">Tổng</span>
        <span class="score-val" :class="overallScore >= 80 ? 'good' : overallScore >= 60 ? 'warn' : 'bad'">
          {{ Number(overallScore).toFixed(0) }}
        </span>
      </div>
      <div v-for="axis in data.axes" :key="axis.code" class="score-item">
        <span class="score-label">{{ axis.label }}</span>
        <div class="score-bar-group">
          <div class="score-bar-track">
            <div
              class="score-bar-fill"
              :class="(axis.score ?? 0) >= 80 ? 'good' : (axis.score ?? 0) >= 60 ? 'warn' : 'bad'"
              :style="{ width: (axis.score ?? 0) + '%' }"
            />
          </div>
          <span class="score-val" :class="(axis.score ?? 0) >= 80 ? 'good' : (axis.score ?? 0) >= 60 ? 'warn' : 'bad'">
            {{ axis.score != null ? Number(axis.score).toFixed(0) : '—' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.spider-chart-wrapper {
  display: flex;
  align-items: center;
  gap: 2.5rem;
}
.chart-container {
  flex-shrink: 0;
}
.score-summary {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  flex: 1;
  min-width: 200px;
  max-width: 320px;
}
.score-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--p-surface-border);
}
.overall-row {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
  border-bottom: 2px solid var(--p-surface-border);
  padding-bottom: 0.75rem;
  margin-bottom: 0.125rem;
}
.overall-row .score-val {
  font-size: 1.5rem;
}
.score-label {
  font-weight: 600;
  font-size: 0.85rem;
}
.score-bar-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.score-bar-track {
  flex: 1;
  height: 6px;
  background: var(--p-surface-200);
  border-radius: 3px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.score-bar-fill.good { background: var(--p-green-500); }
.score-bar-fill.warn { background: var(--p-orange-500); }
.score-bar-fill.bad { background: var(--p-red-500); }
.score-val {
  font-weight: 800;
  font-size: 1rem;
  min-width: 2rem;
  text-align: right;
}
.score-val.good { color: var(--p-green-500); }
.score-val.warn { color: var(--p-orange-500); }
.score-val.bad { color: var(--p-red-500); }
</style>
