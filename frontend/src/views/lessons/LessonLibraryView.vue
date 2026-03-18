<script setup>
/**
 * LessonLibraryView.vue — Lesson Learned Library.
 *
 * Master-detail layout: filters + DataTable on left, LessonDetailDrawer on right.
 * Includes similar-search panel (F08.4) via tab toggle.
 */

import { ref, onMounted, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Toast from 'primevue/toast'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LessonDetailDrawer from '@/components/lessons/LessonDetailDrawer.vue'
import LessonFormDialog from '@/components/lessons/LessonFormDialog.vue'
import { useAuthStore } from '@/stores/auth.js'
import * as lessonService from '@/services/lessonService.js'

const toast = useToast()
const authStore = useAuthStore()

// ── Data ──────────────────────────────────────────────────────
const lessons = ref([])
const lessonsTotal = ref(0)
const loading = ref(false)

const similarLessons = ref([])
const similarTotal = ref(0)
const loadingSimilar = ref(false)

// ── Filters (Library) ─────────────────────────────────────────
const filterFarmType = ref(null)
const filterIssueType = ref(null)
const filterConfidence = ref(null)
const filterStatus = ref(null)
const filterTag = ref(null)

const farmTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Nái (Sow)', value: 'sow' },
  { label: 'Thịt (Finisher)', value: 'finisher' },
  { label: 'Nái–Thịt (Farrow-to-finish)', value: 'farrow_to_finish' },
  { label: 'Hậu bị (Gilt)', value: 'gilt' },
  { label: 'Đực giống (Boar stud)', value: 'boar_stud' },
]

const issueTypeOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Vệ sinh cổng', value: 'vehicle_hygiene' },
  { label: 'Vi phạm lộ trình', value: 'route_violation' },
  { label: 'Xử lý heo chết', value: 'dead_animal_disposal' },
  { label: 'Kiểm soát dịch hại', value: 'pest_control' },
  { label: 'An toàn nguồn nước', value: 'water_safety' },
]

const confidenceOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Nghi ngờ', value: 'suspected' },
  { label: 'Có thể', value: 'probable' },
  { label: 'Xác nhận', value: 'confirmed' },
]

const statusOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Nháp', value: 'draft' },
  { label: 'Đã xác nhận', value: 'validated' },
  { label: 'Lưu trữ', value: 'archived' },
  { label: 'Lỗi thời', value: 'obsolete' },
]

// ── Filters (Similar search) ─────────────────────────────────
const simFarmType = ref(null)
const simOwnershipType = ref(null)
const simIssueType = ref(null)
const simAreaType = ref(null)
const simRouteType = ref(null)
const simSeason = ref(null)

const ownershipOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Gia công', value: 'contract' },
  { label: 'Tự nuôi', value: 'company_owned' },
]

const seasonOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Mùa mưa', value: 'rainy' },
  { label: 'Mùa khô', value: 'dry' },
  { label: 'Chuyển mùa', value: 'transition' },
]

// ── Tabs, drawer, dialog ─────────────────────────────────────
const activeTab = ref('library')
const drawerVisible = ref(false)
const selectedLessonId = ref(null)
const formDialogVisible = ref(false)
const editingLesson = ref(null)

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(() => {
  loadLessons()
})

watch([filterFarmType, filterIssueType, filterConfidence, filterStatus, filterTag], () => {
  loadLessons()
})

async function loadLessons() {
  loading.value = true
  try {
    const params = { page_size: 50 }
    if (filterFarmType.value) params.farm_type = filterFarmType.value
    if (filterIssueType.value) params.issue_type = filterIssueType.value
    if (filterConfidence.value) params.confidence_level = filterConfidence.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterTag.value) params.tag = filterTag.value

    const result = await lessonService.listLessons(params)
    lessons.value = result.data || []
    lessonsTotal.value = result.meta?.total || 0
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải danh sách bài học', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function onSearchSimilar() {
  loadingSimilar.value = true
  try {
    const params = { page_size: 50 }
    if (simFarmType.value) params.farm_type = simFarmType.value
    if (simOwnershipType.value) params.ownership_type = simOwnershipType.value
    if (simIssueType.value) params.issue_type = simIssueType.value
    if (simAreaType.value) params.area_type = simAreaType.value
    if (simRouteType.value) params.route_type = simRouteType.value
    if (simSeason.value) params.season = simSeason.value

    const result = await lessonService.searchSimilar(params)
    similarLessons.value = result.data || []
    similarTotal.value = result.meta?.total || 0
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tìm kiếm tương tự', life: 3000 })
  } finally {
    loadingSimilar.value = false
  }
}

function onRowSelect(event) {
  selectedLessonId.value = event.data.id
  drawerVisible.value = true
}

function openCreateDialog() {
  editingLesson.value = null
  formDialogVisible.value = true
}

function onEditLesson(lesson) {
  editingLesson.value = lesson
  drawerVisible.value = false
  formDialogVisible.value = true
}

function onLessonSaved() {
  loadLessons()
  if (activeTab.value === 'similar') onSearchSimilar()
}

function onLessonValidated() {
  loadLessons()
}

function onLessonUpdated() {
  loadLessons()
}

const statusSeverity = {
  draft: 'warn',
  validated: 'success',
  archived: 'secondary',
  obsolete: 'danger',
}

const statusLabels = {
  draft: 'Nháp',
  validated: 'Đã xác nhận',
  archived: 'Lưu trữ',
  obsolete: 'Lỗi thời',
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('vi-VN')
}
</script>

<template>
  <Toast />
  <div class="lesson-library-view">
    <!-- Page header -->
    <div class="page-header">
      <h2>Thư viện Bài học (Lesson Learned)</h2>
      <Button
        v-if="authStore.hasPermission('LESSON_WRITE')"
        label="Tạo Lesson"
        icon="pi pi-plus"
        size="small"
        class="ml-auto"
        @click="openCreateDialog"
      />
    </div>

    <!-- Tab toggle: Library / Similar search -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="library">Thư viện ({{ lessonsTotal }})</Tab>
        <Tab value="similar">Tìm kiếm tương tự</Tab>
      </TabList>
      <TabPanels>
        <!-- ═══ Library tab ════════════════════════════════════ -->
        <TabPanel value="library">
          <!-- Filters -->
          <div class="filter-bar">
            <div class="filter-item">
              <label>Loại trại</label>
              <Select
                v-model="filterFarmType"
                :options="farmTypeOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Loại vấn đề</label>
              <Select
                v-model="filterIssueType"
                :options="issueTypeOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Độ tin cậy</label>
              <Select
                v-model="filterConfidence"
                :options="confidenceOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Trạng thái</label>
              <Select
                v-model="filterStatus"
                :options="statusOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Tag</label>
              <InputText
                v-model="filterTag"
                placeholder="VD: sow"
                class="filter-select"
                @keyup.enter="loadLessons"
              />
            </div>
          </div>

          <!-- Lesson list DataTable -->
          <DataTable
            :value="lessons"
            :loading="loading"
            stripedRows
            size="small"
            selectionMode="single"
            @rowSelect="onRowSelect"
            :paginator="false"
            scrollable
            scrollHeight="calc(100vh - 22rem)"
          >
            <template #empty>Không có bài học nào phù hợp.</template>
            <Column field="lesson_no" header="Mã" style="width: 140px">
              <template #body="{ data }">
                <span class="lesson-no-cell">{{ data.lesson_no }}</span>
              </template>
            </Column>
            <Column field="title" header="Tiêu đề" />
            <Column field="confidence_level" header="Độ tin cậy" style="width: 120px">
              <template #body="{ data }">
                <StatusBadge :value="data.confidence_level" type="confidence" />
              </template>
            </Column>
            <Column field="status" header="Trạng thái" style="width: 120px">
              <template #body="{ data }">
                <Tag :value="statusLabels[data.status] || data.status" :severity="statusSeverity[data.status] || 'info'" />
              </template>
            </Column>
            <Column field="created_at" header="Ngày tạo" style="width: 110px">
              <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
            </Column>
          </DataTable>
        </TabPanel>

        <!-- ═══ Similar search tab ═════════════════════════════ -->
        <TabPanel value="similar">
          <div class="filter-bar">
            <div class="filter-item">
              <label>Loại trại</label>
              <Select
                v-model="simFarmType"
                :options="farmTypeOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Sở hữu</label>
              <Select
                v-model="simOwnershipType"
                :options="ownershipOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Loại vấn đề</label>
              <Select
                v-model="simIssueType"
                :options="issueTypeOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item">
              <label>Mùa vụ</label>
              <Select
                v-model="simSeason"
                :options="seasonOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tất cả"
                class="filter-select"
              />
            </div>
            <div class="filter-item filter-action">
              <Button label="Tìm kiếm" icon="pi pi-search" size="small" :loading="loadingSimilar" @click="onSearchSimilar" />
            </div>
          </div>

          <!-- Similar results DataTable -->
          <DataTable
            :value="similarLessons"
            :loading="loadingSimilar"
            stripedRows
            size="small"
            selectionMode="single"
            @rowSelect="onRowSelect"
            :paginator="false"
            scrollable
            scrollHeight="calc(100vh - 22rem)"
          >
            <template #empty>Chưa có kết quả. Chọn bộ lọc và nhấn Tìm kiếm.</template>
            <Column field="lesson_no" header="Mã" style="width: 140px">
              <template #body="{ data }">
                <span class="lesson-no-cell">{{ data.lesson_no }}</span>
              </template>
            </Column>
            <Column field="title" header="Tiêu đề" />
            <Column field="confidence_level" header="Độ tin cậy" style="width: 120px">
              <template #body="{ data }">
                <StatusBadge :value="data.confidence_level" type="confidence" />
              </template>
            </Column>
            <Column field="status" header="Trạng thái" style="width: 120px">
              <template #body="{ data }">
                <Tag :value="statusLabels[data.status] || data.status" :severity="statusSeverity[data.status] || 'info'" />
              </template>
            </Column>
            <Column field="created_at" header="Ngày tạo" style="width: 110px">
              <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Detail drawer -->
    <LessonDetailDrawer
      v-model:visible="drawerVisible"
      :lessonId="selectedLessonId"
      @validated="onLessonValidated"
      @edit="onEditLesson"
      @updated="onLessonUpdated"
    />

    <!-- Create/Edit dialog -->
    <LessonFormDialog
      v-model:visible="formDialogVisible"
      :lesson="editingLesson"
      @saved="onLessonSaved"
    />
  </div>
</template>

<style scoped>
.lesson-library-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.page-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}
.page-header h2 {
  margin: 0;
}
.ml-auto {
  margin-left: auto;
}

/* ── Filter bar ──────────────────────────────────────── */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.75rem 0;
  align-items: flex-end;
}
.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.filter-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}
.filter-select {
  min-width: 10rem;
}
.filter-action {
  justify-content: flex-end;
}

/* ── Table ───────────────────────────────────────────── */
.lesson-no-cell {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}
</style>
