<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment.js'
import * as scorecardService from '@/services/scorecardService.js'
import * as assessmentService from '@/services/assessmentService.js'
import * as trustScoreService from '@/services/trustScoreService.js'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Checkbox from 'primevue/checkbox'
import ProgressBar from 'primevue/progressbar'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SpiderChart from '@/components/charts/SpiderChart.vue'
import { useToast } from 'primevue/usetoast'

const route = useRoute()
const router = useRouter()
const store = useAssessmentStore()
const toast = useToast()

const assessmentId = computed(() => route.params.id)
const templateSections = ref([])
const activeSectionIndex = ref(0)
const itemResults = ref({}) // scorecard_item_id → result data
const saving = ref(false)
const showSpider = ref(false)
const comparisonSpider = ref(null)
const trustScoreResult = ref(null)

const assessment = computed(() => store.currentAssessment)
const isDraft = computed(() => assessment.value?.status === 'draft')
const isSubmitted = computed(() => ['submitted', 'reviewed', 'locked'].includes(assessment.value?.status))

const activeSection = computed(() => templateSections.value[activeSectionIndex.value])
const totalItems = computed(() => templateSections.value.reduce((sum, s) => sum + (s.items?.length || 0), 0))
const completedItems = computed(() => Object.keys(itemResults.value).length)
const progressPercent = computed(() => totalItems.value ? Math.round((completedItems.value / totalItems.value) * 100) : 0)

onMounted(async () => {
  await store.fetchAssessment(assessmentId.value)
  if (assessment.value) {
    await loadTemplate()
    initResults()
    if (isSubmitted.value) {
      await store.fetchSpiderChart(assessmentId.value)
      showSpider.value = true
      await loadComparison()
    }
  }
})

async function loadTemplate() {
  try {
    const tmpl = await scorecardService.getTemplate(assessment.value.template_id)
    templateSections.value = tmpl.sections || []
  } catch {
    templateSections.value = []
  }
}

function initResults() {
  const map = {}
  if (assessment.value?.item_results) {
    for (const r of assessment.value.item_results) {
      map[r.scorecard_item_id] = {
        scorecard_item_id: r.scorecard_item_id,
        response_value_text: r.response_value_text,
        response_value_numeric: r.response_value_numeric != null ? Number(r.response_value_numeric) : null,
        awarded_score: Number(r.awarded_score),
        is_non_compliant: r.is_non_compliant,
        note: r.note || '',
        area_id: r.area_id,
      }
    }
  }
  itemResults.value = map
}

function getResult(itemId) {
  if (!itemResults.value[itemId]) {
    itemResults.value[itemId] = {
      scorecard_item_id: itemId,
      response_value_text: null,
      response_value_numeric: null,
      awarded_score: 0,
      is_non_compliant: false,
      note: '',
      area_id: null,
    }
  }
  return itemResults.value[itemId]
}

function onScoreChange(item) {
  const r = getResult(item.id)
  // Auto-set non_compliant if below threshold_fail
  if (item.threshold_fail != null && r.awarded_score < Number(item.threshold_fail)) {
    r.is_non_compliant = true
  }
}

async function saveDraft() {
  saving.value = true
  try {
    const items = Object.values(itemResults.value).filter((r) => r.awarded_score != null)
    await store.bulkUpsertItems(assessmentId.value, items)
    toast.add({ severity: 'success', summary: 'Đã lưu nháp', life: 2000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi lưu', detail: e.response?.data?.error?.message || 'Lỗi lưu nháp', life: 5000 })
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  try {
    // Save items first
    const items = Object.values(itemResults.value).filter((r) => r.awarded_score != null)
    await store.bulkUpsertItems(assessmentId.value, items)
    // Then submit
    await store.submitAssessment(assessmentId.value)
    await store.fetchSpiderChart(assessmentId.value)
    showSpider.value = true
    await loadComparison()
    toast.add({ severity: 'success', summary: 'Đã nộp đánh giá', detail: `Điểm tổng: ${assessment.value.overall_score}`, life: 5000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi nộp', detail: e.response?.data?.error?.message || 'Lỗi nộp đánh giá', life: 5000 })
  } finally {
    saving.value = false
  }
}

function sectionProgress(section) {
  if (!section.items?.length) return 0
  const filled = section.items.filter((it) => itemResults.value[it.id]).length
  return Math.round((filled / section.items.length) * 100)
}

async function loadComparison() {
  const a = assessment.value
  if (!a) return
  // Load comparison spider data if trust_gap_basis_id exists
  if (a.trust_gap_basis_id) {
    try {
      comparisonSpider.value = await assessmentService.getSpiderChart(a.trust_gap_basis_id)
    } catch { comparisonSpider.value = null }
  }
  // Fetch trust score for this farm
  try {
    trustScoreResult.value = await trustScoreService.getLatestTrustScore(a.farm_id)
  } catch { trustScoreResult.value = null }
}

function sectionTypeLabel(t) {
  const map = { hardware: 'Hạ tầng', software: 'Quy trình', behavior: 'Hành vi', monitoring: 'Giám sát', other: 'Khác' }
  return map[t] || t
}

// ── Bottom summary computeds (wireframe §4.4) ──
const flaggedItems = computed(() => Object.values(itemResults.value).filter((r) => r.is_non_compliant).length)
const killerFlaggedItems = computed(() => {
  const killerIds = new Set()
  for (const section of templateSections.value) {
    for (const item of section.items || []) {
      if (item.is_killer_related) killerIds.add(item.id)
    }
  }
  return Object.values(itemResults.value).filter((r) => r.is_non_compliant && killerIds.has(r.scorecard_item_id)).length
})
const scorePreview = computed(() => {
  const results = Object.values(itemResults.value)
  if (!results.length) return null
  const total = results.reduce((s, r) => s + (r.awarded_score || 0), 0)
  const max = results.reduce((s, r) => {
    const item = allItemsFlat.value.find((i) => i.id === r.scorecard_item_id)
    return s + (item ? Number(item.max_score) : 5)
  }, 0)
  return max > 0 ? Math.round((total / max) * 100) : null
})
const allItemsFlat = computed(() => templateSections.value.flatMap((s) => s.items || []))

// ── Low-scoring items (wireframe §4.5) ──
const lowScoringItems = computed(() => {
  const items = []
  for (const section of templateSections.value) {
    for (const item of section.items || []) {
      const r = itemResults.value[item.id]
      if (!r) continue
      const pct = Number(item.max_score) > 0 ? (r.awarded_score / Number(item.max_score)) * 100 : 0
      if (pct < 60) {
        items.push({ code: item.code, question: item.question_text, score: r.awarded_score, max: Number(item.max_score), pct, sectionName: section.name })
      }
    }
  }
  return items.sort((a, b) => a.pct - b.pct).slice(0, 10)
})

function goNextSection() {
  if (activeSectionIndex.value < templateSections.value.length - 1) {
    activeSectionIndex.value++
  }
}

function goPrevSection() {
  if (activeSectionIndex.value > 0) {
    activeSectionIndex.value--
  }
}
</script>

<template>
  <div v-if="assessment" class="assessment-form">
    <!-- Header card -->
    <div class="header-card">
      <div class="form-header">
        <div class="header-left">
          <Button icon="pi pi-arrow-left" text rounded @click="router.push('/assessments')" class="back-btn" />
          <div>
            <h2>{{ assessment.farm_name_snapshot || assessment.performed_by_name_snapshot || 'Đánh giá' }}</h2>
            <div class="header-meta">
              <StatusBadge :value="assessment.status" :label="assessment.status_label" />
              <Tag :value="assessment.assessment_type_label || assessment.assessment_type" severity="secondary" rounded />
              <span class="meta-divider">|</span>
              <span><i class="pi pi-calendar" /> {{ new Date(assessment.assessment_date).toLocaleDateString('vi-VN') }}</span>
              <span v-if="assessment.performed_by_name_snapshot" class="meta-divider">|</span>
              <span v-if="assessment.performed_by_name_snapshot"><i class="pi pi-user" /> {{ assessment.performed_by_name_snapshot }}</span>
            </div>
          </div>
        </div>
        <div class="header-right" v-if="assessment.overall_score != null">
          <div class="overall-score" :class="assessment.overall_score >= 80 ? 'good' : assessment.overall_score >= 60 ? 'warn' : 'bad'">
            {{ Number(assessment.overall_score).toFixed(0) }}
          </div>
          <span class="overall-label">Điểm tổng</span>
        </div>
      </div>

      <!-- Progress -->
      <div class="progress-section">
        <span class="progress-label">{{ completedItems }}/{{ totalItems }} items</span>
        <div class="progress-bar-wrapper">
          <ProgressBar :value="progressPercent" :showValue="true" style="height: 1.5rem" />
        </div>
      </div>
    </div>

    <!-- Spider Chart (visible after submit) -->
    <div v-if="showSpider && store.spiderData" class="spider-section">
      <div class="section-title">
        <i class="pi pi-chart-pie" />
        <h3>Biểu đồ đánh giá</h3>
      </div>
      <SpiderChart
        :data="store.spiderData"
        :comparison="comparisonSpider"
        :overallScore="assessment.overall_score != null ? Number(assessment.overall_score) : null"
      />
      <!-- Trust Score display -->
      <div v-if="trustScoreResult" class="trust-score-bar">
        <div class="ts-info">
          <span class="ts-label">Trust Score</span>
          <span class="ts-value" :class="trustScoreResult.trust_score >= 80 ? 'ts-good' : trustScoreResult.trust_score >= 60 ? 'ts-warn' : 'ts-bad'">
            {{ Math.round(trustScoreResult.trust_score) }}
          </span>
          <span v-if="trustScoreResult.trend" class="ts-trend">
            <i :class="trustScoreResult.trend === 'up' ? 'pi pi-arrow-up' : trustScoreResult.trend === 'down' ? 'pi pi-arrow-down' : 'pi pi-minus'" />
          </span>
        </div>
        <div class="ts-note" v-if="trustScoreResult.note">{{ trustScoreResult.note }}</div>
      </div>
    </div>

    <!-- Main content: section nav + items -->
    <div class="content-grid">
      <!-- Section Navigator -->
      <div class="section-nav">
        <div class="nav-title">Các phần</div>
        <div
          v-for="(section, idx) in templateSections"
          :key="section.id"
          class="nav-section-item"
          :class="{ active: idx === activeSectionIndex }"
          @click="activeSectionIndex = idx"
        >
          <div class="nav-section-name">
            <Tag :value="sectionTypeLabel(section.section_type)" :severity="idx === activeSectionIndex ? 'primary' : 'secondary'" rounded />
            <span>{{ section.name }}</span>
          </div>
          <div class="nav-progress-row">
            <ProgressBar :value="sectionProgress(section)" style="height: 10px; flex: 1" />
            <span class="nav-pct">{{ sectionProgress(section) }}%</span>
          </div>
        </div>
      </div>

      <!-- Items -->
      <div class="items-panel" v-if="activeSection">
        <h3>{{ activeSection.name }}</h3>
        <div v-for="item in activeSection.items" :key="item.id" class="item-card" :class="{ 'non-compliant': getResult(item.id).is_non_compliant }">
          <div class="item-header">
            <span class="item-code">{{ item.code }}</span>
            <Tag v-if="item.is_killer_related" value="KILLER" severity="danger" rounded />
          </div>
          <p class="item-question">{{ item.question_text }}</p>
          <div v-if="item.guidance_text" class="item-guidance">
            <i class="pi pi-info-circle" /> {{ item.guidance_text }}
          </div>

          <div class="item-inputs">
            <div class="input-group">
              <label>Điểm (max {{ item.max_score }})</label>
              <InputNumber
                v-model="getResult(item.id).awarded_score"
                :min="0"
                :max="Number(item.max_score)"
                :disabled="!isDraft"
                @update:modelValue="onScoreChange(item)"
                class="w-full"
              />
            </div>
            <div class="input-group note-group">
              <label>Ghi chú</label>
              <Textarea v-model="getResult(item.id).note" rows="1" :disabled="!isDraft" class="w-full" autoResize />
            </div>
          </div>

          <div v-if="getResult(item.id).is_non_compliant" class="non-compliant-flag">
            <i class="pi pi-exclamation-triangle" /> Không đạt
          </div>
        </div>
        <div v-if="isDraft" class="section-nav-buttons">
          <Button label="Trước" icon="pi pi-arrow-left" text size="small" :disabled="activeSectionIndex === 0" @click="goPrevSection" />
          <Button label="Tiếp" icon="pi pi-arrow-right" iconPos="right" text size="small" :disabled="activeSectionIndex >= templateSections.length - 1" @click="goNextSection" />
        </div>
      </div>
    </div>

    <!-- Bottom summary (wireframe §4.4: score preview | flagged items | killer flags) -->
    <div class="bottom-summary">
      <div class="summary-item">
        <div class="summary-icon">
          <i class="pi pi-chart-line" />
        </div>
        <div class="summary-detail">
          <span class="summary-label">Điểm dự kiến</span>
          <strong :class="scorePreview != null && scorePreview >= 80 ? 'score-good' : scorePreview >= 60 ? 'score-warn' : 'score-bad'" class="summary-value">{{ scorePreview != null ? scorePreview + '%' : '—' }}</strong>
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-icon warn">
          <i class="pi pi-flag" />
        </div>
        <div class="summary-detail">
          <span class="summary-label">Không đạt</span>
          <strong class="summary-value">{{ flaggedItems }}</strong>
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-icon danger">
          <i class="pi pi-exclamation-triangle" />
        </div>
        <div class="summary-detail">
          <span class="summary-label">Killer flags</span>
          <strong class="summary-value">{{ killerFlaggedItems }}</strong>
        </div>
      </div>
    </div>

    <!-- Low-scoring items (wireframe §4.5) -->
    <div v-if="showSpider && lowScoringItems.length" class="low-scoring-section">
      <div class="section-title">
        <i class="pi pi-exclamation-circle" style="color: var(--p-red-500)" />
        <h3>Items điểm thấp</h3>
      </div>
      <DataTable :value="lowScoringItems" size="small" stripedRows>
        <Column field="code" header="Mã" style="width: 10%" />
        <Column field="question" header="Tiêu chí" />
        <Column field="sectionName" header="Phần" style="width: 12%" />
        <Column header="Điểm" style="width: 10%">
          <template #body="{ data }">
            <span class="score-bad">{{ data.score }}/{{ data.max }}</span>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Action buttons (wireframe §4.5: Create case | Export | Open farm profile) -->
    <div v-if="showSpider" class="assessment-actions">
      <Button label="Tạo Case" icon="pi pi-exclamation-circle" severity="warn" size="small" disabled />
      <Button label="Xuất báo cáo" icon="pi pi-download" severity="secondary" size="small" disabled />
      <Button label="Xem hồ sơ trại" icon="pi pi-external-link" size="small" @click="router.push(`/farms/${assessment.farm_id}`)" />
    </div>

    <!-- Bottom form actions -->
    <div class="form-actions" v-if="isDraft">
      <Button label="Lưu nháp" icon="pi pi-save" severity="secondary" @click="saveDraft" :loading="saving" />
      <Button label="Nộp đánh giá" icon="pi pi-send" @click="handleSubmit" :loading="saving" />
    </div>
  </div>
  <div v-else class="loading-container">
    <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
  </div>
</template>

<style scoped>
.assessment-form {
  /* no max-width — match other pages */
}

/* ── Header Card ── */
.header-card {
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
}
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.back-btn { flex-shrink: 0; }
.header-left h2 { margin: 0; font-size: 1.25rem; }
.header-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  margin-top: 0.375rem;
  flex-wrap: wrap;
}
.header-meta i { font-size: 0.75rem; }
.meta-divider { opacity: 0.4; }
.header-right {
  text-align: center;
  padding: 0.5rem 1.25rem;
  border-left: 2px solid var(--p-surface-border);
  margin-left: 1rem;
}
.overall-score {
  font-size: 2.75rem;
  font-weight: 800;
  line-height: 1;
}
.overall-score.good { color: var(--p-green-500); }
.overall-score.warn { color: var(--p-orange-500); }
.overall-score.bad { color: var(--p-red-500); }
.overall-label { font-size: 0.7rem; color: var(--p-text-muted-color); text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Progress ── */
.progress-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--p-surface-border);
}
.progress-label {
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  color: var(--p-text-muted-color);
}
.progress-bar-wrapper { flex: 1; }

/* ── Spider Section ── */
.spider-section {
  margin-bottom: 1.25rem;
  padding: 1.25rem;
  background: var(--p-surface-card);
  border-radius: 12px;
  border: 1px solid var(--p-surface-border);
}
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.section-title h3 { margin: 0; font-size: 1rem; }
.section-title i { font-size: 1.1rem; color: var(--p-primary-color); }

/* ── Content Grid ── */
.content-grid {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 1.25rem;
  min-height: 400px;
}

/* ── Section Navigator ── */
.section-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: sticky;
  top: 1rem;
  align-self: start;
}
.nav-title {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--p-text-color);
  padding: 0 0.75rem;
  margin-bottom: 0.25rem;
}
.nav-section-item {
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid var(--p-surface-border);
  transition: all 0.2s ease;
  background: var(--p-surface-card);
}
.nav-section-item:hover {
  background: var(--p-surface-hover);
  border-color: var(--p-surface-300);
}
.nav-section-item.active {
  background: color-mix(in srgb, var(--p-primary-color) 8%, transparent);
  border-color: var(--p-primary-color);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--p-primary-color) 20%, transparent);
}
.nav-section-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  color: var(--p-text-color);
}
.nav-progress-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.nav-pct {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  min-width: 2rem;
  text-align: right;
}

/* ── Items Panel ── */
.items-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.items-panel h3 { margin: 0 0 0.25rem; font-size: 1.1rem; color: var(--p-text-color); }

.item-card {
  padding: 1.25rem;
  border: 1px solid var(--p-surface-border);
  border-radius: 10px;
  background: var(--p-surface-card);
  transition: box-shadow 0.15s;
}
.item-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.item-card.non-compliant {
  border-color: var(--p-red-300);
  background: color-mix(in srgb, var(--p-red-500) 5%, var(--p-surface-card));
  border-left: 3px solid var(--p-red-500);
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.375rem;
}
.item-code {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--p-primary-color);
}
.item-question {
  margin: 0 0 0.625rem;
  font-size: 0.9rem;
  line-height: 1.5;
}
.item-guidance {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  margin-bottom: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--p-surface-100);
  border-radius: 6px;
  border-left: 3px solid var(--p-primary-200);
}
.item-inputs {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.input-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}
.note-group { flex: 1; }
.non-compliant-flag {
  margin-top: 0.625rem;
  padding: 0.375rem 0.75rem;
  background: color-mix(in srgb, var(--p-red-500) 10%, transparent);
  border-radius: 6px;
  color: var(--p-red-500);
  font-weight: 600;
  font-size: 0.8rem;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.section-nav-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--p-surface-border);
}

/* ── Bottom Summary ── */
.bottom-summary {
  display: flex;
  gap: 1.5rem;
  padding: 1rem 1.25rem;
  margin-top: 1.25rem;
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.summary-icon {
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: color-mix(in srgb, var(--p-primary-color) 12%, transparent);
  color: var(--p-primary-color);
  font-size: 0.9rem;
  flex-shrink: 0;
}
.summary-icon.warn {
  background: color-mix(in srgb, var(--p-orange-500) 12%, transparent);
  color: var(--p-orange-500);
}
.summary-icon.danger {
  background: color-mix(in srgb, var(--p-red-500) 12%, transparent);
  color: var(--p-red-500);
}
.summary-detail {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.summary-label {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.summary-value {
  font-size: 1.1rem;
}
.score-good { color: var(--p-green-500); }
.score-warn { color: var(--p-orange-500); }
.score-bad { color: var(--p-red-500); }

/* ── Low Scoring ── */
.low-scoring-section {
  margin-top: 1.25rem;
  padding: 1.25rem;
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 12px;
}
.low-scoring-section h3 { margin: 0; font-size: 1rem; }

/* ── Action buttons ── */
.assessment-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

/* ── Form Actions ── */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--p-surface-border);
}

.loading-container { display: flex; justify-content: center; padding: 4rem; }

/* ── Mobile Responsive ── */
@media (max-width: 768px) {
  .header-card {
    padding: 1rem;
    border-radius: 8px;
  }
  .form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .header-right {
    border-left: none;
    margin-left: 0;
    padding: 0.5rem 0 0;
    border-top: 1px solid var(--p-surface-border);
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-align: left;
  }
  .overall-score {
    font-size: 2rem;
  }
  .header-left h2 {
    font-size: 1.05rem;
  }
  .header-meta {
    font-size: 0.75rem;
  }

  .content-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  .section-nav {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  .nav-title {
    grid-column: 1 / -1;
    padding: 0 0.25rem;
  }
  .nav-section-item {
    padding: 0.5rem 0.625rem;
    border-radius: 8px;
  }
  .nav-section-name {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    font-size: 0.75rem;
    margin-bottom: 0.375rem;
  }
  .nav-section-name .p-tag {
    font-size: 0.65rem;
    padding: 0.125rem 0.375rem;
  }
  .nav-progress-row {
    gap: 0.375rem;
  }
  .nav-pct {
    font-size: 0.65rem;
    min-width: auto;
  }

  .item-card {
    padding: 1rem;
  }
  .item-inputs {
    flex-direction: column;
    gap: 0.75rem;
  }
  .input-group {
    width: 100%;
  }

  .bottom-summary {
    flex-wrap: wrap;
    gap: 1rem;
    padding: 0.875rem 1rem;
  }
  .summary-item {
    min-width: calc(50% - 0.5rem);
  }

  .assessment-actions {
    flex-wrap: wrap;
  }
  .form-actions {
    flex-direction: column;
  }
  .form-actions .p-button {
    width: 100%;
  }

  .low-scoring-section {
    padding: 1rem;
    overflow-x: auto;
  }

  .spider-section {
    padding: 1rem;
  }
}

/* ── Trust Score Bar ── */
.trust-score-bar {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: var(--p-surface-card);
  border: 1px solid var(--p-surface-border);
  border-radius: 8px;
}

.ts-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ts-label {
  font-weight: 600;
  font-size: 0.85rem;
}

.ts-value {
  font-size: 1.5rem;
  font-weight: 800;
}

.ts-good { color: var(--p-green-500); }
.ts-warn { color: var(--p-orange-500); }
.ts-bad { color: var(--p-red-500); }

.ts-trend { font-size: 0.85rem; }
.ts-note { font-size: 0.8rem; color: var(--p-text-muted-color); margin-top: 0.25rem; }
</style>
