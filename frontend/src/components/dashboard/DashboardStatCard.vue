<script setup>
import { computed } from 'vue'
import Card from 'primevue/card'
import Tag from 'primevue/tag'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  icon: {
    type: String,
    default: 'pi pi-info-circle'
  },
  trend: {
    type: Number,
    default: null // positive = up, negative = down, null = no trend
  },
  trendLabel: {
    type: String,
    default: ''
  },
  severity: {
    type: String,
    default: null // 'success', 'warning', 'danger', 'info'
  },
  backgroundColor: {
    type: String,
    default: 'var(--p-surface-card)'
  },
  onClick: {
    type: Function,
    default: null
  }
})

const isTrendPositive = computed(() => props.trend > 0)
const isTrendNegative = computed(() => props.trend < 0)
const trendIcon = computed(() => {
  if (props.trend > 0) return 'pi pi-arrow-up'
  if (props.trend < 0) return 'pi pi-arrow-down'
  return null
})
const trendSeverity = computed(() => {
  if (!props.trend) return null
  return isTrendPositive.value ? 'success' : 'danger'
})

const iconGradient = computed(() => {
  const severityMap = {
    'success': 'linear-gradient(135deg, var(--p-green-500), var(--p-green-600))',
    'warning': 'linear-gradient(135deg, var(--p-orange-500), var(--p-orange-600))',
    'danger': 'linear-gradient(135deg, var(--p-red-500), var(--p-red-600))',
    'info': 'linear-gradient(135deg, var(--p-blue-500), var(--p-blue-600))'
  }
  return severityMap[props.severity] || 'linear-gradient(135deg, var(--p-primary-500), var(--p-primary-600))'
})
</script>

<template>
  <Card
    class="dashboard-stat-card"
    :style="{ backgroundColor }"
    :class="{ 'cursor-pointer': onClick }"
    @click="onClick"
  >
    <template #header>
      <div class="stat-card-header">
        <div class="stat-icon-wrapper" :style="{ background: iconGradient }">
          <i :class="icon"></i>
        </div>
        <h3 class="stat-title">{{ title }}</h3>
      </div>
    </template>

    <template #content>
      <div class="stat-content">
        <div class="stat-value-section">
          <p class="stat-value">{{ value }}</p>
          <div v-if="trend !== null" class="trend-badge">
            <Tag
              :severity="trendSeverity"
              :value="`${trend > 0 ? '+' : ''}${trend}%`"
              :icon="trendIcon"
            />
            <span v-if="trendLabel" class="trend-label">{{ trendLabel }}</span>
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.dashboard-stat-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: all 0.2s ease;
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.dashboard-stat-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.dashboard-stat-card.cursor-pointer {
  cursor: pointer;
}

.stat-card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.stat-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 12px;
  font-size: 1.75rem;
  color: var(--p-surface-card);
  flex-shrink: 0;
}

.stat-title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex: 1;
}

.stat-content {
  padding: 0 1rem 1rem;
}

.stat-value-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-value {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--p-text-color);
  line-height: 1;
}

.trend-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.trend-label {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  font-weight: 500;
}

/* Responsive */
@media screen and (max-width: 768px) {
  .stat-card-header {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .stat-icon-wrapper {
    width: 40px;
    height: 40px;
    font-size: 1.5rem;
  }

  .stat-title {
    font-size: 0.75rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .stat-content {
    padding: 0 0.75rem 0.75rem;
  }
}
</style>
