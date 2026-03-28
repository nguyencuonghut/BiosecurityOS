<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import StatusBadge from '@/components/common/StatusBadge.vue'
import FarmFormDialog from '@/views/farms/FarmFormDialog.vue'
import FarmAreaPanel from '@/views/farms/FarmAreaPanel.vue'
import FarmRoutePanel from '@/views/farms/FarmRoutePanel.vue'
import FarmRiskPointPanel from '@/views/farms/FarmRiskPointPanel.vue'
import FarmFloorplanPanel from '@/views/farms/FarmFloorplanPanel.vue'
import FarmLessonPanel from '@/views/farms/FarmLessonPanel.vue'
import FarmDashboardPanel from '@/components/dashboard/FarmDashboardPanel.vue'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'
import { useTrustScoreStore } from '@/stores/trustScore.js'
import * as floorplanService from '@/services/floorplanService.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const farmStore = useFarmStore()
const authStore = useAuthStore()
const trustScoreStore = useTrustScoreStore()

const activeTab = ref('overview')
const showEditDialog = ref(false)
const floorplanCount = ref(0)

const farm = computed(() => farmStore.currentFarm)

onMounted(async () => {
  await farmStore.fetchRegions()
  await farmStore.fetchFarm(route.params.id)
  await Promise.all([
    farmStore.fetchAreas(route.params.id),
    farmStore.fetchRoutes(route.params.id),
    farmStore.fetchRiskPoints(route.params.id),
    trustScoreStore.fetchLatest(route.params.id),
    floorplanService.listFloorplans(route.params.id).then(fps => { floorplanCount.value = fps.length }).catch(() => {}),
  ])
})

function regionName(regionId) {
  const r = farmStore.regions.find((r) => r.id === regionId)
  return r?.name || '—'
}

function farmTypeLabel(val) {
  const m = { sow: 'Nái', finisher: 'Thịt', mixed: 'Hỗn hợp', other: 'Khác' }
  return m[val] || val
}

function ownershipLabel(val) {
  const m = { company: 'Công ty', lease: 'Thuê', contract: 'Hợp đồng', other: 'Khác' }
  return m[val] || val
}

function trustScoreColor(score) {
  if (score == null) return 'muted'
  if (score >= 80) return 'green'
  if (score >= 60) return 'yellow'
  return 'red'
}

function trustScoreSeverity(score) {
  if (score == null) return 'secondary'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warn'
  return 'danger'
}

function openEdit() {
  showEditDialog.value = true
}

async function onSaved() {
  showEditDialog.value = false
  toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã cập nhật trại', life: 3000 })
  await farmStore.fetchFarm(route.params.id)
}
</script>

<template>
  <Toast />
  <div class="farm-detail" v-if="farm">
    <!-- Header -->
    <div class="detail-header">
      <div class="header-left">
        <Button icon="pi pi-arrow-left" text rounded severity="secondary" @click="router.push({ name: 'Farms' })" />
        <div>
          <h2>{{ farm.name }}</h2>
          <div class="header-meta">
            <Tag :value="farm.code" severity="secondary" />
            <span>{{ regionName(farm.region_id) }}</span>
            <span>·</span>
            <span>{{ farmTypeLabel(farm.farm_type) }}</span>
            <span>·</span>
            <span>{{ ownershipLabel(farm.ownership_type) }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <StatusBadge :value="farm.baseline_risk_level" type="risk" />
        <StatusBadge :value="farm.operational_status" type="status" />
        <Button
          v-if="authStore.hasPermission('FARM_WRITE')"
          label="Sửa"
          icon="pi pi-pencil"
          severity="secondary"
          outlined
          @click="openEdit"
        />
      </div>
    </div>

    <!-- Overview info cards -->
    <div class="info-cards">
      <div class="info-card">
        <div class="info-label">Công suất</div>
        <div class="info-value">{{ farm.capacity_headcount != null ? farm.capacity_headcount.toLocaleString() + ' đầu' : '—' }}</div>
      </div>
      <div class="info-card">
        <div class="info-label">Địa chỉ</div>
        <div class="info-value">{{ farm.address || '—' }}</div>
      </div>
      <div class="info-card">
        <div class="info-label">Tọa độ</div>
        <div class="info-value">
          {{ farm.latitude != null && farm.longitude != null ? `${farm.latitude}, ${farm.longitude}` : '—' }}
        </div>
      </div>
      <div class="info-card">
        <div class="info-label">Ngày mở</div>
        <div class="info-value">{{ farm.opened_at || '—' }}</div>
      </div>
      <div class="info-card trust-score-card" :class="'ts-' + trustScoreColor(trustScoreStore.latestScore?.trust_score)">
        <div class="info-label">Trust Score</div>
        <div class="trust-score-value" v-if="trustScoreStore.latestScore">
          <span class="ts-number">{{ Math.round(trustScoreStore.latestScore.trust_score) }}</span>
          <Tag :value="trustScoreStore.latestScore.trust_score >= 80 ? 'Tốt' : trustScoreStore.latestScore.trust_score >= 60 ? 'Trung bình' : 'Thấp'" :severity="trustScoreSeverity(trustScoreStore.latestScore.trust_score)" />
          <div class="ts-trend" v-if="trustScoreStore.latestScore.trend">
            <i :class="trustScoreStore.latestScore.trend === 'up' ? 'pi pi-arrow-up' : trustScoreStore.latestScore.trend === 'down' ? 'pi pi-arrow-down' : 'pi pi-minus'" :style="{ color: trustScoreStore.latestScore.trend === 'up' ? 'var(--p-green-500)' : trustScoreStore.latestScore.trend === 'down' ? 'var(--p-red-500)' : 'var(--p-text-muted-color)' }"></i>
            <span v-if="trustScoreStore.latestScore.change">{{ trustScoreStore.latestScore.change > 0 ? '+' : '' }}{{ trustScoreStore.latestScore.change.toFixed(1) }}</span>
          </div>
        </div>
        <div class="info-value" v-else>Chưa có</div>
      </div>
    </div>

    <!-- Structural Risk Note -->
    <div class="risk-note-section" v-if="farm.structural_risk_note">
      <div class="risk-note-label">
        <i class="pi pi-exclamation-triangle" style="color: var(--p-orange-500)"></i>
        Ghi chú rủi ro cấu trúc
      </div>
      <div class="risk-note-text">{{ farm.structural_risk_note }}</div>
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="overview">Tổng quan</Tab>
        <Tab value="0">Khu vực ({{ farmStore.areas.length }})</Tab>
        <Tab value="1">Lộ trình ({{ farmStore.routes.length }})</Tab>
        <Tab value="2">Điểm rủi ro ({{ farmStore.riskPoints.length }})</Tab>
        <Tab value="3">Floorplan ({{ floorplanCount }})</Tab>
        <Tab value="4">Bài học</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="overview">
          <FarmDashboardPanel :farmId="farm.id" />
        </TabPanel>
        <TabPanel value="0">
          <FarmAreaPanel :farmId="farm.id" />
        </TabPanel>
        <TabPanel value="1">
          <FarmRoutePanel :farmId="farm.id" />
        </TabPanel>
        <TabPanel value="2">
          <FarmRiskPointPanel :farmId="farm.id" />
        </TabPanel>
        <TabPanel value="3">
          <FarmFloorplanPanel :farmId="farm.id" />
        </TabPanel>
        <TabPanel value="4">
          <FarmLessonPanel :farmId="farm.id" :farmType="farm.farm_type" :ownershipType="farm.ownership_type" />
        </TabPanel>
      </TabPanels>
    </Tabs>

    <FarmFormDialog
      v-model:visible="showEditDialog"
      :farm="farm"
      :regions="farmStore.regions"
      @saved="onSaved"
    />
  </div>

  <div v-else class="loading-msg">
    <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
    <p>Đang tải thông tin trại...</p>
  </div>
</template>

<style scoped>
.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.header-left h2 {
  margin: 0 0 0.25rem;
  font-size: 1.35rem;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.info-card {
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  margin-bottom: 0.25rem;
}

.info-value {
  font-weight: 600;
  font-size: 0.9rem;
}

.risk-note-section {
  background: var(--p-surface-card);
  border: 1px solid var(--p-orange-200);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
}

.risk-note-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--p-text-color);
  margin-bottom: 0.35rem;
}

.risk-note-text {
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
  line-height: 1.5;
}

.placeholder {
  text-align: center;
  padding: 3rem;
  color: var(--p-text-muted-color);
}

.loading-msg {
  text-align: center;
  padding: 4rem 0;
  color: var(--p-text-muted-color);
}

/* Trust Score card */
.trust-score-card {
  position: relative;
}

.trust-score-card.ts-green { border-left: 3px solid var(--p-green-500); }
.trust-score-card.ts-yellow { border-left: 3px solid var(--p-yellow-500); }
.trust-score-card.ts-red { border-left: 3px solid var(--p-red-500); }

.trust-score-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.ts-number {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}

.ts-trend {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
