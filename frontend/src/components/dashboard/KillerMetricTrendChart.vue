<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import Card from 'primevue/card'
import { useLayout } from '@/layouts/composables/layout.js'

use([BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const { layoutState } = useLayout()

// Reactive text/axis color that follows dark mode
const textColor    = computed(() => layoutState.darkMode ? '#e2e8f0' : '#374151')
const mutedColor   = computed(() => layoutState.darkMode ? '#94a3b8' : '#6b7280')
const borderColor  = computed(() => layoutState.darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)')
const tooltipBg    = computed(() => layoutState.darkMode ? '#1e293b' : '#ffffff')
const tooltipBorder= computed(() => layoutState.darkMode ? '#334155' : '#e5e7eb')

const option = computed(() => {
  if (!props.data.length) return {}

  const months = [...new Set(props.data.map((d) => d.month))].sort()
  const metrics = [...new Set(props.data.map((d) => d.metric_name))]

  const colors = ['#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6', '#EC4899']

  const series = metrics.map((metric, idx) => ({
    name: metric,
    type: 'bar',
    stack: 'total',
    emphasis: { focus: 'series' },
    itemStyle: { color: colors[idx % colors.length] },
    data: months.map((m) => {
      const entry = props.data.find((d) => d.month === m && d.metric_name === metric)
      return entry ? entry.event_count : 0
    }),
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: tooltipBg.value,
      borderColor: tooltipBorder.value,
      textStyle: { color: textColor.value },
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: textColor.value },
      pageTextStyle: { color: mutedColor.value },
      pageIconColor: textColor.value,
      pageIconInactiveColor: mutedColor.value,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: months.map((m) => {
        const d = new Date(m)
        return `${d.getMonth() + 1}/${d.getFullYear()}`
      }),
      axisLine:  { lineStyle: { color: borderColor.value } },
      axisTick:  { lineStyle: { color: borderColor.value } },
      axisLabel: { color: mutedColor.value },
    },
    yAxis: {
      type: 'value',
      name: 'Số sự kiện',
      nameTextStyle: { color: mutedColor.value },
      axisLabel: { color: mutedColor.value },
      splitLine: { lineStyle: { color: borderColor.value } },
    },
    series,
  }
})
</script>

<template>
  <Card class="km-trend-card">
    <template #title>
      <i class="pi pi-exclamation-triangle"></i>
      Xu hướng Killer Metrics
    </template>

    <template #content>
      <div v-if="data.length" class="chart-container">
        <VChart :option="option" autoresize style="height: 320px" />
      </div>
      <div v-else class="empty-state">
        <i class="pi pi-info-circle"></i>
        <span>Chưa có dữ liệu killer metrics</span>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.km-trend-card {
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.chart-container {
  width: 100%;
}

.empty-state {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  justify-content: center;
  color: var(--p-text-muted-color);
}
</style>
