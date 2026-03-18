<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import DashboardStatCard from '@/components/dashboard/DashboardStatCard.vue'
import DashboardBenchmark from '@/components/dashboard/DashboardBenchmark.vue'
import TrustGapPanel from '@/components/dashboard/TrustGapPanel.vue'
import KillerMetricTrendChart from '@/components/dashboard/KillerMetricTrendChart.vue'
import ScarHotspotTable from '@/components/dashboard/ScarHotspotTable.vue'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'

const router = useRouter()
const store = useDashboardStore()

onMounted(() => {
  store.fetchDashboard()
})

const viewAllFarms = () => router.push({ name: 'Farms' })
const viewAllCases = () => router.push({ name: 'CaseQueue' })
</script>

<template>
  <div class="dashboard-container">
    <!-- Page Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">Dashboard điều hành</h1>
        <p class="page-subtitle">Tổng quan hệ thống quản lý An toàn sinh học</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <!-- Error -->
    <Message v-if="store.error" severity="error" :closable="false">
      {{ store.error }}
    </Message>

    <template v-if="store.executive">
      <!-- KPI Cards Grid -->
      <section class="kpi-section">
        <h2 class="section-title">Chỉ số chính</h2>
        <div class="kpi-grid">
          <DashboardStatCard
            title="Tổng số trại"
            :value="store.executive.farm_count"
            icon="pi pi-building"
            severity="info"
            @click="viewAllFarms"
          />
          <DashboardStatCard
            title="Điểm trung bình"
            :value="store.executive.avg_score != null ? `${store.executive.avg_score.toFixed(1)}/100` : '—'"
            icon="pi pi-chart-bar"
            :severity="(store.executive.avg_score ?? 0) >= 75 ? 'success' : 'warning'"
            @click="viewAllFarms"
          />
          <DashboardStatCard
            title="Trại rủi ro cao"
            :value="store.executive.high_risk_farms"
            icon="pi pi-exclamation-triangle"
            severity="danger"
            @click="viewAllFarms"
          />
          <DashboardStatCard
            title="Case mở"
            :value="store.executive.open_cases"
            icon="pi pi-folder-open"
            severity="warning"
            @click="viewAllCases"
          />
          <DashboardStatCard
            title="Task quá hạn"
            :value="store.executive.overdue_tasks"
            icon="pi pi-clock"
            severity="danger"
            @click="viewAllCases"
          />
          <DashboardStatCard
            title="Killer Metrics"
            :value="store.executive.killer_metric_open"
            icon="pi pi-heart-fill"
            severity="danger"
            @click="viewAllCases"
          />
          <DashboardStatCard
            title="Trại tin cậy thấp"
            :value="store.executive.low_trust_sites"
            icon="pi pi-shield"
            severity="warning"
            @click="viewAllFarms"
          />
        </div>
      </section>

      <!-- Row: Trust Gap + Benchmark -->
      <div class="dashboard-row">
        <div class="dashboard-col">
          <TrustGapPanel :data="store.trustGaps" />
        </div>
        <div class="dashboard-col">
          <DashboardBenchmark :data="store.benchmark" />
        </div>
      </div>

      <!-- Row: Killer Metric Trend + Scar Hotspot -->
      <div class="dashboard-row">
        <div class="dashboard-col">
          <KillerMetricTrendChart :data="store.killerMetricsTrend" />
        </div>
        <div class="dashboard-col">
          <ScarHotspotTable :data="store.scarHotspots" />
        </div>
      </div>

      <!-- Quick Actions -->
      <section class="quick-actions-section">
        <h2 class="section-title">Hành động nhanh</h2>
        <div class="actions-grid">
          <Button
            label="Quản lý Case"
            icon="pi pi-briefcase"
            class="action-button"
            @click="router.push({ name: 'CaseQueue' })"
          />
          <Button
            label="Xem Scorecard"
            icon="pi pi-chart-pie"
            class="action-button"
            severity="secondary"
            @click="router.push({ name: 'Scorecards' })"
          />
          <Button
            label="Xem Bài học"
            icon="pi pi-book"
            class="action-button"
            severity="secondary"
            @click="router.push({ name: 'LessonLibrary' })"
          />
          <Button
            label="Scar Map"
            icon="pi pi-map"
            class="action-button"
            severity="secondary"
            @click="router.push({ name: 'ScarMap' })"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 0;
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  padding: 2rem;
  background: linear-gradient(135deg, var(--p-primary-color) 0%, var(--p-primary-600) 100%);
  border-radius: 12px;
  color: var(--p-primary-contrast-color);
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0 0 0.5rem;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.page-subtitle {
  margin: 0;
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 500;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 3rem;
}

/* Section */
.section-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--p-text-color);
}

/* KPI Grid */
.kpi-section {
  padding: 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

/* Dashboard Rows */
.dashboard-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.dashboard-col {
  min-width: 0;
}

/* Quick Actions */
.quick-actions-section {
  padding: 2rem;
  background: var(--p-surface-card);
  border-radius: 12px;
  border: 1px solid var(--p-surface-border);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}

.action-button {
  width: 100%;
  font-weight: 600;
}

/* Responsive */
@media screen and (max-width: 991px) {
  .dashboard-container {
    gap: 1.5rem;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
  }

  .dashboard-row {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 600px) {
  .dashboard-container {
    gap: 1rem;
  }

  .dashboard-header {
    padding: 1.5rem;
  }

  .page-title {
    font-size: 1.25rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 1rem;
    margin-bottom: 1rem;
  }
}
</style>
