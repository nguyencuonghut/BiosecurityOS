<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import DashboardStatCard from '@/components/dashboard/DashboardStatCard.vue'
import DashboardBenchmark from '@/components/dashboard/DashboardBenchmark.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const router = useRouter()

// Mock data for Executive Summary
const dashboardData = ref({
  farm_count: 20,
  avg_score: 78.4,
  high_risk_farms: 4,
  open_cases: 23,
  overdue_tasks: 11,
  killer_metric_open: 2,
  low_trust_sites: 3,
  last_updated: new Date().toLocaleString('vi-VN')
})

// Mock farm list for quick access
const recentFarms = ref([
  {
    id: 'farm_001',
    code: 'F001',
    name: 'Trại nái Hải Dương',
    score: 85.2,
    status: 'active',
    risk_level: 'medium',
    open_cases: 2
  },
  {
    id: 'farm_002',
    code: 'F002',
    name: 'Trại thịt Thanh Hóa',
    score: 72.1,
    status: 'active',
    risk_level: 'high',
    open_cases: 5
  },
  {
    id: 'farm_003',
    code: 'F003',
    name: 'Trại nái Bắc Ninh',
    score: 81.5,
    status: 'active',
    risk_level: 'low',
    open_cases: 1
  },
  {
    id: 'farm_004',
    code: 'F004',
    name: 'Trại thịt Hà Nam',
    score: 68.3,
    status: 'active',
    risk_level: 'high',
    open_cases: 8
  }
])

// Mock open cases list
const openCases = ref([
  {
    id: 'case_001',
    case_no: 'C00001',
    farm_name: 'Trại nái Hải Dương',
    title: 'Điểm số X thấp - Hạ tầng',
    priority: 'P1',
    status: 'open',
    created_at: '2026-03-15'
  },
  {
    id: 'case_002',
    case_no: 'C00002',
    farm_name: 'Trại thịt Thanh Hóa',
    title: 'Killer Metric: Vi phạm luồng',
    priority: 'P0',
    status: 'open',
    created_at: '2026-03-14'
  }
])

// Get severity for risk level
const getRiskSeverity = (level) => {
  const map = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger'
  }
  return map[level] || 'info'
}

// Get severity for priority
const getPrioritySeverity = (priority) => {
  const map = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': 'info',
    'P3': 'success'
  }
  return map[priority] || 'info'
}

// Get status badge severity
const getStatusSeverity = (status) => {
  const map = {
    'open': 'danger',
    'in_progress': 'warning',
    'closed': 'success'
  }
  return map[status] || 'info'
}

// Navigate to farm detail
const navigateToFarm = (farmId) => {
  router.push({ name: 'FarmDetail', params: { id: farmId } })
}

// Navigate to case detail
const navigateToCase = (caseId) => {
  router.push({ name: 'CaseDetail', params: { id: caseId } })
}

// View all farms
const viewAllFarms = () => {
  router.push({ name: 'FarmList' })
}

// View all cases
const viewAllCases = () => {
  router.push({ name: 'CaseQueue' })
}
</script>

<template>
  <div class="dashboard-container">
    <!-- Page Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">Executive Dashboard</h1>
        <p class="page-subtitle">Tổng quan hệ thống quản lý An toàn sinh học</p>
      </div>
      <div class="header-actions">
        <span class="last-update">Cập nhật: {{ dashboardData.last_updated }}</span>
      </div>
    </div>

    <!-- KPI Cards Grid -->
    <section class="kpi-section">
      <h2 class="section-title">Chỉ số chính</h2>
      <div class="kpi-grid">
        <!-- Total Farms -->
        <DashboardStatCard
          title="Tổng số trại"
          :value="dashboardData.farm_count"
          icon="pi pi-building"
          severity="info"
          @click="viewAllFarms"
        />

        <!-- Average Score -->
        <DashboardStatCard
          title="Điểm trung bình"
          :value="`${dashboardData.avg_score}/100`"
          icon="pi pi-chart-bar"
          :trend="2.3"
          trend-label="tháng này"
          :severity="dashboardData.avg_score >= 75 ? 'success' : 'warning'"
          @click="viewAllFarms"
        />

        <!-- High Risk Farms -->
        <DashboardStatCard
          title="Trại rủi ro cao"
          :value="dashboardData.high_risk_farms"
          icon="pi pi-exclamation-triangle"
          severity="danger"
          @click="viewAllFarms"
        />

        <!-- Open Cases -->
        <DashboardStatCard
          title="Case mở"
          :value="dashboardData.open_cases"
          icon="pi pi-folder-open"
          :trend="-4.1"
          trend-label="tuần này"
          severity="warning"
          @click="viewAllCases"
        />

        <!-- Overdue Tasks -->
        <DashboardStatCard
          title="Task quá hạn"
          :value="dashboardData.overdue_tasks"
          icon="pi pi-clock"
          severity="danger"
          @click="viewAllCases"
        />

        <!-- Killer Metrics -->
        <DashboardStatCard
          title="Killer Metrics"
          :value="dashboardData.killer_metric_open"
          icon="pi pi-heart-fill"
          severity="danger"
          @click="viewAllCases"
        />

        <!-- Low Trust Sites -->
        <DashboardStatCard
          title="Trại tin cậy thấp"
          :value="dashboardData.low_trust_sites"
          icon="pi pi-shield"
          severity="warning"
          @click="viewAllFarms"
        />
      </div>
    </section>

    <!-- Recent Farms Section -->
    <section class="recent-farms-section">
      <div class="section-header">
        <h2 class="section-title">Trại được theo dõi</h2>
        <Button
          label="Xem tất cả"
          icon="pi pi-arrow-right"
          severity="secondary"
          text
          @click="viewAllFarms"
        />
      </div>

      <div class="farms-grid">
        <Card
          v-for="farm in recentFarms"
          :key="farm.id"
          class="farm-card"
          @click="navigateToFarm(farm.id)"
        >
          <template #content>
            <div class="farm-card-content">
              <!-- Farm Header -->
              <div class="farm-header">
                <div class="farm-info">
                  <h3 class="farm-name">{{ farm.name }}</h3>
                  <p class="farm-code">{{ farm.code }}</p>
                </div>
                <Tag
                  :value="farm.risk_level.toUpperCase()"
                  :severity="getRiskSeverity(farm.risk_level)"
                  class="farm-risk-tag"
                />
              </div>

              <!-- Farm Score -->
              <div class="farm-score-section">
                <div class="score-display">
                  <span class="score-value">{{ farm.score }}</span>
                  <span class="score-label">/100</span>
                </div>
                <div class="score-bar">
                  <div
                    class="score-bar-fill"
                    :style="{ width: `${farm.score}%` }"
                    :class="`severity-${getRiskSeverity(farm.risk_level)}`"
                  ></div>
                </div>
              </div>

              <!-- Farm Stats -->
              <div class="farm-stats">
                <div class="stat">
                  <i class="pi pi-briefcase"></i>
                  <span>{{ farm.open_cases }} case</span>
                </div>
                <div class="stat">
                  <i :class="`pi ${farm.status === 'active' ? 'pi-check-circle' : 'pi-times-circle'}`"></i>
                  <span>{{ farm.status === 'active' ? 'Hoạt động' : 'Dừng' }}</span>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <!-- Open Cases Section -->
    <section class="open-cases-section">
      <div class="section-header">
        <h2 class="section-title">Case cần xử lý</h2>
        <Button
          label="Xem tất cả"
          icon="pi pi-arrow-right"
          severity="secondary"
          text
          @click="viewAllCases"
        />
      </div>

      <Card>
        <template #content>
          <DataTable
            :value="openCases"
            class="cases-table"
            :rows="5"
            paginator
            responsive-layout="scroll"
            table-style="min-width: 50rem"
            striped-rows
          >
            <Column field="case_no" header="Mã Case" style="width: 10%">
              <template #body="slotProps">
                <a
                  href="javascript:void(0)"
                  class="case-link"
                  @click="navigateToCase(slotProps.data.id)"
                >
                  {{ slotProps.data.case_no }}
                </a>
              </template>
            </Column>

            <Column field="farm_name" header="Trại" style="width: 25%"></Column>

            <Column field="title" header="Tiêu đề" style="width: 35%"></Column>

            <Column field="priority" header="Ưu tiên" style="width: 10%">
              <template #body="slotProps">
                <Tag
                  :value="slotProps.data.priority"
                  :severity="getPrioritySeverity(slotProps.data.priority)"
                />
              </template>
            </Column>

            <Column field="status" header="Trạng thái" style="width: 10%">
              <template #body="slotProps">
                <Tag
                  :value="slotProps.data.status.replace('_', ' ').toUpperCase()"
                  :severity="getStatusSeverity(slotProps.data.status)"
                />
              </template>
            </Column>

            <Column field="created_at" header="Ngày tạo" style="width: 10%"></Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- Benchmark Section -->
    <section class="benchmark-section">
      <DashboardBenchmark />
    </section>

    <!-- Quick Actions Section -->
    <section class="quick-actions-section">
      <h2 class="section-title">Hành động nhanh</h2>
      <div class="actions-grid">
        <Button
          label="Tạo Case"
          icon="pi pi-plus"
          class="action-button"
          @click="router.push({ name: 'CaseCreate' })"
        />
        <Button
          label="Xem Scorecard"
          icon="pi pi-chart-pie"
          class="action-button"
          severity="secondary"
          @click="router.push({ name: 'ScorecardList' })"
        />
        <Button
          label="Xem Bài học"
          icon="pi pi-book"
          class="action-button"
          severity="secondary"
          @click="router.push({ name: 'Lessons' })"
        />
        <Button
          label="Báo cáo"
          icon="pi pi-file-pdf"
          class="action-button"
          severity="secondary"
          @click="router.push({ name: 'Reports' })"
        />
      </div>
    </section>
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
  margin: 0 -1rem -2rem -1rem;
  margin-bottom: 0;
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

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.last-update {
  font-size: 0.875rem;
  opacity: 0.85;
}

/* Section Styling */
.section-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header .section-title {
  margin-bottom: 0;
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

/* Farms Grid */
.recent-farms-section {
  padding: 0;
}

.farms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.farm-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}

.farm-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.farm-card-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.farm-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.farm-info {
  flex: 1;
}

.farm-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.farm-code {
  margin: 0.25rem 0 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  font-weight: 500;
}

.farm-risk-tag {
  font-weight: 600;
}

.farm-score-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.score-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.score-label {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.score-bar {
  height: 8px;
  background: var(--p-surface-border);
  border-radius: 4px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.score-bar-fill.severity-success {
  background: var(--p-green-500);
}

.score-bar-fill.severity-warning {
  background: var(--p-orange-500);
}

.score-bar-fill.severity-danger {
  background: var(--p-red-500);
}

.farm-stats {
  display: flex;
  gap: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-surface-border);
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.stat i {
  font-size: 1rem;
  color: var(--p-primary-color);
}

/* Cases Section */
.open-cases-section {
  padding: 0;
}

.cases-table {
  width: 100%;
}

.case-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
}

.case-link:hover {
  color: var(--p-primary-600);
  text-decoration: underline;
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
    text-align: left;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
  }

  .farms-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
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

  .farms-grid {
    grid-template-columns: 1fr;
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

