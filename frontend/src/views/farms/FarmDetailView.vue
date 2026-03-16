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
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const farmStore = useFarmStore()
const authStore = useAuthStore()

const activeTab = ref('0')
const showEditDialog = ref(false)

const farm = computed(() => farmStore.currentFarm)

onMounted(async () => {
  await farmStore.fetchRegions()
  await farmStore.fetchFarm(route.params.id)
  await Promise.all([
    farmStore.fetchAreas(route.params.id),
    farmStore.fetchRoutes(route.params.id),
    farmStore.fetchRiskPoints(route.params.id),
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
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="0">Khu vực ({{ farmStore.areas.length }})</Tab>
        <Tab value="1">Lộ trình ({{ farmStore.routes.length }})</Tab>
        <Tab value="2">Điểm rủi ro ({{ farmStore.riskPoints.length }})</Tab>
        <Tab value="3">Floorplan</Tab>
      </TabList>
      <TabPanels>
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
          <div class="placeholder">Floorplan sẽ triển khai trong Sprint 07</div>
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
</style>
