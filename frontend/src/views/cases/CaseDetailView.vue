<script setup>
/**
 * F05.2 — Case Detail + RCA Workspace (wireframe §4.7)
 * Tabs: Overview | RCA | Timeline
 * Actions: Assign expert, Change status, Create RCA, Approve RCA
 */
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
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Breadcrumb from 'primevue/breadcrumb'
import Timeline from 'primevue/timeline'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import Step from 'primevue/step'
import Avatar from 'primevue/avatar'
import Skeleton from 'primevue/skeleton'
import Divider from 'primevue/divider'
import { useRiskCaseStore } from '@/stores/riskCase.js'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const store = useRiskCaseStore()
const farmStore = useFarmStore()
const authStore = useAuthStore()

const activeTab = ref('0')
const caseData = computed(() => store.currentCase)

// ── Breadcrumb model ──
const breadcrumbItems = computed(() => [
  { label: 'Danh sách Case', command: () => router.push('/cases') },
  { label: caseData.value?.case_no || '...' },
])
const breadcrumbHome = { icon: 'pi pi-clipboard', command: () => router.push('/cases') }

// ── State machine ──
const VALID_TRANSITIONS = {
  open: ['triage', 'cancelled'],
  triage: ['in_analysis', 'cancelled'],
  in_analysis: ['actioning', 'triage', 'cancelled'],
  actioning: ['monitoring', 'in_analysis', 'cancelled'],
  monitoring: ['closed', 'actioning'],
}

const showStatusDialog = ref(false)
const targetStatus = ref(null)

function nextActions(status) {
  return VALID_TRANSITIONS[status] || []
}

function openStatusDialog(target) {
  targetStatus.value = target
  showStatusDialog.value = true
}

async function confirmStatusChange() {
  try {
    await store.changeStatus(caseData.value.id, targetStatus.value, caseData.value.version)
    toast.add({ severity: 'success', summary: 'Thành công', detail: `Đã chuyển sang ${statusLabel(targetStatus.value)}`, life: 3000 })
    showStatusDialog.value = false
    await store.fetchTimeline(caseData.value.id)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Assign Expert ──
const showAssignDialog = ref(false)
const assignUserId = ref(null)
const userOptions = ref([])

async function openAssignDialog() {
  // Fetch users for assignment (lazy import the user service)
  try {
    const { listUsers } = await import('@/services/userService.js')
    const result = await listUsers({ page_size: 100 })
    userOptions.value = result.data.filter(u => u.status === 'active')
  } catch {
    userOptions.value = []
  }
  assignUserId.value = caseData.value?.assigned_expert_user_id || null
  showAssignDialog.value = true
}

async function submitAssign() {
  try {
    await store.assignExpert(caseData.value.id, assignUserId.value)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã phân công chuyên gia', life: 3000 })
    showAssignDialog.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── RCA CRUD ──
const showRcaForm = ref(false)
const editingRca = ref(null)
const rcaForm = ref({
  method: '5_why', problem_statement: '', impact_scope: '',
  direct_cause: '', system_cause: '', behavioral_cause: '',
  structural_cause: '', monitoring_cause: '', external_factor: '',
  conclusion_confidence: 'medium',
})

const rcaMethodOptions = [
  { label: '5 Why', value: '5_why' },
  { label: 'Fishbone', value: 'fishbone' },
  { label: 'CAPA', value: 'capa' },
  { label: 'Khác', value: 'other' },
]

const confidenceOptions = [
  { label: 'Thấp', value: 'low' },
  { label: 'Trung bình', value: 'medium' },
  { label: 'Cao', value: 'high' },
  { label: 'Xác nhận', value: 'confirmed' },
]

function openCreateRca() {
  editingRca.value = null
  rcaForm.value = {
    method: '5_why', problem_statement: '', impact_scope: '',
    direct_cause: '', system_cause: '', behavioral_cause: '',
    structural_cause: '', monitoring_cause: '', external_factor: '',
    conclusion_confidence: 'medium',
  }
  showRcaForm.value = true
}

function openEditRca(rca) {
  editingRca.value = rca
  rcaForm.value = {
    method: rca.method,
    problem_statement: rca.problem_statement,
    impact_scope: rca.impact_scope || '',
    direct_cause: rca.direct_cause || '',
    system_cause: rca.system_cause || '',
    behavioral_cause: rca.behavioral_cause || '',
    structural_cause: rca.structural_cause || '',
    monitoring_cause: rca.monitoring_cause || '',
    external_factor: rca.external_factor || '',
    conclusion_confidence: rca.conclusion_confidence,
  }
  showRcaForm.value = true
}

async function submitRca() {
  try {
    if (editingRca.value) {
      await store.updateRcaRecord(editingRca.value.id, rcaForm.value)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã cập nhật RCA', life: 3000 })
    } else {
      await store.createRcaRecord(caseData.value.id, rcaForm.value)
      toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã tạo RCA', life: 3000 })
    }
    showRcaForm.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

async function approveRca(rca) {
  try {
    await store.approveRca(rca.id)
    toast.add({ severity: 'success', summary: 'Đã phê duyệt', detail: 'RCA đã được phê duyệt', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── RCA Factors ──
const showFactorForm = ref(false)
const factorRcaId = ref(null)
const factorForm = ref({ factor_group: 'people', factor_text: '', confidence_level: 'medium', is_primary: false })

const factorGroupOptions = [
  { label: 'Con người', value: 'people' },
  { label: 'Quy trình', value: 'process' },
  { label: 'Địa điểm', value: 'place' },
  { label: 'Thiết bị', value: 'equipment' },
  { label: 'Môi trường', value: 'environment' },
  { label: 'Giám sát', value: 'monitoring' },
  { label: 'Bên ngoài', value: 'external' },
]

function openAddFactor(rcaId) {
  factorRcaId.value = rcaId
  factorForm.value = { factor_group: 'people', factor_text: '', confidence_level: 'medium', is_primary: false }
  showFactorForm.value = true
}

async function submitFactor() {
  try {
    await store.createFactor(factorRcaId.value, factorForm.value)
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã thêm yếu tố', life: 3000 })
    showFactorForm.value = false
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

async function removeFactor(factorId) {
  try {
    await store.deleteFactor(factorId)
    toast.add({ severity: 'success', summary: 'Đã xóa', detail: 'Đã xóa yếu tố', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Có lỗi xảy ra', life: 5000 })
  }
}

// ── Helpers ──
function priorityColor(p) {
  const m = { P0: 'danger', P1: 'warn', P2: 'info', P3: 'secondary' }
  return m[p] || 'secondary'
}
function severityColor(s) {
  const m = { critical: 'danger', high: 'warn', medium: 'info', low: 'success' }
  return m[s] || 'secondary'
}
function statusColor(s) {
  const m = { open: 'danger', triage: 'warn', in_analysis: 'info', actioning: 'warn', monitoring: 'info', closed: 'success', cancelled: 'secondary' }
  return m[s] || 'secondary'
}
function statusLabel(s) {
  const m = { open: 'Mới mở', triage: 'Phân loại', in_analysis: 'Đang RCA', actioning: 'Thực thi', monitoring: 'Theo dõi', closed: 'Đã đóng', cancelled: 'Đã hủy' }
  return m[s] || s
}
function caseTypeLabel(t) {
  const m = { low_score: 'Điểm thấp', killer_event: 'Killer Event', scar: 'Scar', manual: 'Thủ công' }
  return m[t] || t
}
function farmName(farmId) {
  return farmStore.farms.find(f => f.id === farmId)?.name || '—'
}
function confidenceLabel(c) {
  const m = { low: 'Thấp', medium: 'Trung bình', high: 'Cao', confirmed: 'Xác nhận' }
  return m[c] || c
}
function factorGroupLabel(g) {
  const m = { people: 'Con người', process: 'Quy trình', place: 'Địa điểm', equipment: 'Thiết bị', environment: 'Môi trường', monitoring: 'Giám sát', external: 'Bên ngoài' }
  return m[g] || g
}
function methodLabel(m) {
  const map = { '5_why': '5 Why', fishbone: 'Fishbone', capa: 'CAPA', other: 'Khác' }
  return map[m] || m
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function timelineIcon(type) {
  const m = { case_opened: 'pi pi-folder-open', case_closed: 'pi pi-check-circle', rca_created: 'pi pi-search', rca_approved: 'pi pi-verified', killer_event: 'pi pi-bolt' }
  return m[type] || 'pi pi-circle'
}
function timelineColor(type) {
  const m = { case_opened: 'var(--p-blue-500)', case_closed: 'var(--p-green-500)', rca_created: 'var(--p-orange-500)', rca_approved: 'var(--p-green-500)', killer_event: 'var(--p-red-500)' }
  return m[type] || 'var(--p-text-muted-color)'
}

// ── Status pipeline ──
const STATUS_PIPELINE = ['open', 'triage', 'in_analysis', 'actioning', 'monitoring', 'closed']
const statusStepIndex = computed(() => {
  if (!caseData.value) return -1
  if (caseData.value.current_status === 'cancelled') return -1
  return STATUS_PIPELINE.indexOf(caseData.value.current_status)
})

// ── Init ──
onMounted(async () => {
  await farmStore.fetchFarms()
  const id = route.params.id
  await store.fetchCase(id)
  await Promise.all([
    store.fetchTimeline(id),
    store.fetchRcaRecords(id),
  ])
})
</script>

<template>
  <Toast />
  <div class="case-detail-page" v-if="caseData">
    <!-- Breadcrumb -->
    <Breadcrumb :model="breadcrumbItems" :home="breadcrumbHome" class="case-breadcrumb" />

    <!-- Case Header -->
    <div class="case-header">
      <div class="header-top">
        <div class="header-title-block">
          <h1 class="case-title">{{ caseData.case_no }} <span class="title-sep">—</span> {{ caseData.title }}</h1>
          <div class="header-tags">
            <Tag :value="caseTypeLabel(caseData.case_type)" severity="secondary" />
            <Tag :value="caseData.priority" :severity="priorityColor(caseData.priority)" />
            <Tag :value="caseData.severity" :severity="severityColor(caseData.severity)" />
          </div>
        </div>
        <div class="header-actions">
          <Button
            v-if="authStore.hasPermission('CASE_ASSIGN')"
            label="Phân công"
            icon="pi pi-user"
            severity="info"
            outlined
            size="small"
            @click="openAssignDialog"
          />
          <Button
            v-for="target in nextActions(caseData.current_status)"
            :key="target"
            :label="statusLabel(target)"
            size="small"
            :severity="statusColor(target)"
            outlined
            @click="openStatusDialog(target)"
          />
        </div>
      </div>

      <!-- Status Pipeline — PrimeVue Stepper (horizontal, read-only) -->
      <div class="pipeline-wrap" v-if="caseData.current_status !== 'cancelled'">
        <Stepper :value="statusStepIndex" linear class="case-stepper">
          <StepList>
            <Step v-for="(step, idx) in STATUS_PIPELINE" :key="step" :value="idx">
              {{ statusLabel(step) }}
            </Step>
          </StepList>
        </Stepper>
      </div>
      <div v-else class="cancelled-banner">
        <i class="pi pi-ban"></i> Case đã bị hủy
      </div>
    </div>

    <!-- Tabs: Overview | RCA | Timeline -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="0"><i class="pi pi-info-circle"></i> Tổng quan</Tab>
        <Tab value="1"><i class="pi pi-search"></i> RCA Workspace</Tab>
        <Tab value="2"><i class="pi pi-clock"></i> Timeline</Tab>
      </TabList>
      <TabPanels>
        <!-- ═══ TAB 0: Overview ═══ -->
        <TabPanel value="0">
          <div class="overview-grid">
            <div class="overview-main">
              <div class="info-card card-accent-blue">
                <div class="card-header-row">
                  <i class="pi pi-file-edit card-icon"></i>
                  <h4>Thông tin case</h4>
                </div>
                <div class="info-rows">
                  <div class="info-row"><label>Trại</label><span>{{ farmName(caseData.farm_id) }}</span></div>
                  <div class="info-row"><label>Loại</label><span>{{ caseTypeLabel(caseData.case_type) }}</span></div>
                  <div class="info-row"><label>Ưu tiên</label><Tag :value="caseData.priority" :severity="priorityColor(caseData.priority)" /></div>
                  <div class="info-row"><label>Nghiêm trọng</label><Tag :value="caseData.severity" :severity="severityColor(caseData.severity)" /></div>
                  <div class="info-row"><label>Trạng thái</label><Tag :value="statusLabel(caseData.current_status)" :severity="statusColor(caseData.current_status)" /></div>
                  <div class="info-row"><label>Ngày mở</label><span>{{ formatDate(caseData.opened_at) }}</span></div>
                  <div class="info-row" v-if="caseData.closed_at"><label>Ngày đóng</label><span>{{ formatDate(caseData.closed_at) }}</span></div>
                  <div class="info-row" v-if="caseData.first_response_due_at"><label>Hạn SLA</label><span class="sla-value">{{ formatDate(caseData.first_response_due_at) }}</span></div>
                </div>
              </div>
              <div class="info-card">
                <div class="card-header-row">
                  <i class="pi pi-align-left card-icon"></i>
                  <h4>Mô tả</h4>
                </div>
                <p class="summary-text">{{ caseData.summary || 'Chưa có mô tả.' }}</p>
              </div>
            </div>
            <div class="overview-side">
              <div class="info-card card-accent-teal">
                <div class="card-header-row">
                  <i class="pi pi-user card-icon"></i>
                  <h4>Chuyên gia phụ trách</h4>
                </div>
                <div v-if="caseData.assigned_expert_user_id" class="expert-badge">
                  <Avatar icon="pi pi-user" shape="circle" class="expert-avatar" />
                  <span class="expert-name">{{ caseData.assigned_expert_name || caseData.assigned_expert_user_id.slice(0, 8) + '…' }}</span>
                </div>
                <div v-else class="empty-inline">
                  <i class="pi pi-user-minus"></i>
                  <span>Chưa phân công</span>
                </div>
              </div>
              <div class="info-card card-accent-orange" v-if="caseData.source_assessment_id || caseData.source_killer_event_id">
                <div class="card-header-row">
                  <i class="pi pi-link card-icon"></i>
                  <h4>Nguồn liên kết</h4>
                </div>
                <div v-if="caseData.source_assessment_id" class="info-row">
                  <label>Assessment</label>
                  <span class="mono">{{ caseData.source_assessment_id.slice(0, 12) }}…</span>
                </div>
                <div v-if="caseData.source_killer_event_id" class="info-row">
                  <label>Killer Event</label>
                  <span class="mono">{{ caseData.source_killer_event_id.slice(0, 12) }}…</span>
                </div>
              </div>
              <div class="info-card card-accent-purple">
                <div class="card-header-row">
                  <i class="pi pi-search card-icon"></i>
                  <h4>Phân tích RCA</h4>
                </div>
                <div class="rca-stat">
                  <span class="rca-stat-num">{{ store.rcaRecords.length }}</span>
                  <span class="rca-stat-label">bản ghi RCA</span>
                </div>
                <Button label="Xem RCA Workspace" icon="pi pi-arrow-right" text size="small" @click="activeTab = '1'" />
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- ═══ TAB 1: RCA Workspace ═══ -->
        <TabPanel value="1">
          <div class="rca-workspace">
            <div class="rca-header">
              <h3><i class="pi pi-search"></i> RCA Workspace</h3>
              <Button
                v-if="authStore.hasPermission('RCA_WRITE')"
                label="Thêm RCA"
                icon="pi pi-plus"
                size="small"
                @click="openCreateRca"
              />
            </div>

            <div v-if="store.rcaRecords.length === 0" class="empty-state">
              <div class="empty-icon-wrap">
                <i class="pi pi-search"></i>
              </div>
              <h4>Chưa có bản ghi RCA</h4>
              <p>Nhấn "Thêm RCA" để bắt đầu phân tích nguyên nhân gốc rễ.</p>
            </div>

            <!-- RCA cards -->
            <div v-for="rca in store.rcaRecords" :key="rca.id" class="rca-card" :class="{ 'rca-approved': rca.approved_at }">
              <div class="rca-card-header">
                <div class="rca-card-title">
                  <Tag :value="methodLabel(rca.method)" severity="info" />
                  <Tag :value="confidenceLabel(rca.conclusion_confidence)" :severity="rca.conclusion_confidence === 'confirmed' ? 'success' : 'secondary'" />
                  <Tag v-if="rca.approved_at" value="Đã duyệt" severity="success" icon="pi pi-check" />
                </div>
                <div class="rca-card-actions">
                  <Button v-if="!rca.approved_at && authStore.hasPermission('RCA_WRITE')" icon="pi pi-pencil" text size="small" @click="openEditRca(rca)" />
                  <Button v-if="!rca.approved_at && authStore.hasPermission('RCA_WRITE')" label="Phê duyệt" icon="pi pi-check" severity="success" size="small" outlined @click="approveRca(rca)" />
                  <Button v-if="!rca.approved_at && authStore.hasPermission('RCA_WRITE')" label="Thêm yếu tố" icon="pi pi-plus" size="small" text @click="openAddFactor(rca.id)" />
                </div>
              </div>

              <div class="rca-body">
                <div class="rca-field"><label>Vấn đề</label><p>{{ rca.problem_statement }}</p></div>
                <div class="rca-causes-grid">
                  <div v-if="rca.direct_cause" class="rca-field"><label>Nguyên nhân trực tiếp</label><p>{{ rca.direct_cause }}</p></div>
                  <div v-if="rca.system_cause" class="rca-field"><label>Nguyên nhân hệ thống</label><p>{{ rca.system_cause }}</p></div>
                  <div v-if="rca.behavioral_cause" class="rca-field"><label>Nguyên nhân hành vi</label><p>{{ rca.behavioral_cause }}</p></div>
                  <div v-if="rca.structural_cause" class="rca-field"><label>Nguyên nhân cấu trúc</label><p>{{ rca.structural_cause }}</p></div>
                  <div v-if="rca.monitoring_cause" class="rca-field"><label>Nguyên nhân giám sát</label><p>{{ rca.monitoring_cause }}</p></div>
                  <div v-if="rca.external_factor" class="rca-field"><label>Yếu tố bên ngoài</label><p>{{ rca.external_factor }}</p></div>
                </div>
                <div v-if="rca.impact_scope" class="rca-field"><label>Phạm vi ảnh hưởng</label><p>{{ rca.impact_scope }}</p></div>
              </div>

              <!-- Factors -->
              <Divider v-if="rca.factors && rca.factors.length" />
              <div v-if="rca.factors && rca.factors.length" class="factors-section">
                <h5><i class="pi pi-list"></i> Yếu tố phân tích</h5>
                <DataTable :value="rca.factors" size="small" class="factor-table" stripedRows>
                  <Column header="Nhóm" style="min-width: 110px">
                    <template #body="{ data }">
                      <Tag :value="factorGroupLabel(data.factor_group)" severity="secondary" />
                    </template>
                  </Column>
                  <Column header="Mô tả" field="factor_text" style="min-width: 200px" />
                  <Column header="Độ tin cậy" style="min-width: 100px">
                    <template #body="{ data }">
                      <Tag :value="confidenceLabel(data.confidence_level)" :severity="data.confidence_level === 'confirmed' ? 'success' : 'secondary'" />
                    </template>
                  </Column>
                  <Column header="Chính" style="width: 70px">
                    <template #body="{ data }">
                      <i v-if="data.is_primary" class="pi pi-star-fill" style="color: var(--p-yellow-500)"></i>
                    </template>
                  </Column>
                  <Column v-if="!rca.approved_at" header="" style="width: 50px">
                    <template #body="{ data }">
                      <Button icon="pi pi-trash" text severity="danger" size="small" @click="removeFactor(data.id)" />
                    </template>
                  </Column>
                </DataTable>
              </div>

              <div class="rca-meta">
                <span><i class="pi pi-calendar"></i> Phân tích: {{ formatDate(rca.analyzed_at) }}</span>
                <span v-if="rca.approved_at"><i class="pi pi-verified"></i> Duyệt: {{ formatDate(rca.approved_at) }}</span>
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- ═══ TAB 2: Timeline ═══ -->
        <TabPanel value="2">
          <div class="timeline-section">
            <h3><i class="pi pi-clock"></i> Timeline</h3>
            <div v-if="store.timeline.length === 0" class="empty-state">
              <div class="empty-icon-wrap"><i class="pi pi-clock"></i></div>
              <h4>Chưa có sự kiện</h4>
              <p>Các hoạt động của case sẽ được ghi lại tại đây.</p>
            </div>
            <Timeline :value="store.timeline" align="left" class="case-timeline" v-else>
              <template #marker="{ item }">
                <div class="tl-marker" :style="{ borderColor: timelineColor(item.event_type) }">
                  <i :class="timelineIcon(item.event_type)" :style="{ color: timelineColor(item.event_type) }"></i>
                </div>
              </template>
              <template #content="{ item }">
                <div class="tl-card">
                  <div class="tl-detail">{{ item.detail }}</div>
                </div>
              </template>
              <template #opposite="{ item }">
                <span class="tl-time">{{ formatDate(item.occurred_at) }}</span>
              </template>
            </Timeline>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- ═══ Status Change Dialog ═══ -->
    <Dialog v-model:visible="showStatusDialog" header="Xác nhận chuyển trạng thái" modal class="responsive-dialog dialog-sm">
      <p>
        Chuyển case <strong>{{ caseData.case_no }}</strong>
        từ <Tag :value="statusLabel(caseData.current_status)" :severity="statusColor(caseData.current_status)" />
        sang <Tag :value="statusLabel(targetStatus)" :severity="statusColor(targetStatus)" /> ?
      </p>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showStatusDialog = false" />
        <Button label="Xác nhận" icon="pi pi-check" @click="confirmStatusChange" />
      </template>
    </Dialog>

    <!-- ═══ Assign Expert Dialog ═══ -->
    <Dialog v-model:visible="showAssignDialog" header="Phân công chuyên gia" modal class="responsive-dialog dialog-sm">
      <div class="form-field">
        <label>Chọn chuyên gia</label>
        <Select v-model="assignUserId" :options="userOptions" optionLabel="full_name" optionValue="id" placeholder="Chọn user" class="w-full" filter />
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showAssignDialog = false" />
        <Button label="Phân công" icon="pi pi-user-plus" @click="submitAssign" :disabled="!assignUserId" />
      </template>
    </Dialog>

    <!-- ═══ RCA Form Dialog ═══ -->
    <Dialog v-model:visible="showRcaForm" :header="editingRca ? 'Sửa RCA' : 'Tạo RCA mới'" modal class="responsive-dialog dialog-lg">
      <div class="rca-form-grid">
        <div class="form-row">
          <div class="form-field">
            <label>Phương pháp</label>
            <Select v-model="rcaForm.method" :options="rcaMethodOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="form-field">
            <label>Độ tin cậy</label>
            <Select v-model="rcaForm.conclusion_confidence" :options="confidenceOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="form-field">
          <label>Vấn đề <span class="req">*</span></label>
          <Textarea v-model="rcaForm.problem_statement" rows="2" class="w-full" placeholder="Mô tả vấn đề cần phân tích..." />
        </div>
        <div class="form-field">
          <label>Phạm vi ảnh hưởng</label>
          <Textarea v-model="rcaForm.impact_scope" rows="2" class="w-full" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Nguyên nhân trực tiếp</label>
            <Textarea v-model="rcaForm.direct_cause" rows="2" class="w-full" />
          </div>
          <div class="form-field">
            <label>Nguyên nhân hệ thống</label>
            <Textarea v-model="rcaForm.system_cause" rows="2" class="w-full" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Nguyên nhân hành vi</label>
            <Textarea v-model="rcaForm.behavioral_cause" rows="2" class="w-full" />
          </div>
          <div class="form-field">
            <label>Nguyên nhân cấu trúc</label>
            <Textarea v-model="rcaForm.structural_cause" rows="2" class="w-full" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>Nguyên nhân giám sát</label>
            <Textarea v-model="rcaForm.monitoring_cause" rows="2" class="w-full" />
          </div>
          <div class="form-field">
            <label>Yếu tố bên ngoài</label>
            <Textarea v-model="rcaForm.external_factor" rows="2" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showRcaForm = false" />
        <Button :label="editingRca ? 'Cập nhật' : 'Tạo RCA'" icon="pi pi-check" @click="submitRca" :disabled="!rcaForm.problem_statement" />
      </template>
    </Dialog>

    <!-- ═══ Factor Dialog ═══ -->
    <Dialog v-model:visible="showFactorForm" header="Thêm yếu tố phân tích" modal class="responsive-dialog dialog-md">
      <div class="form-grid">
        <div class="form-row">
          <div class="form-field">
            <label>Nhóm yếu tố</label>
            <Select v-model="factorForm.factor_group" :options="factorGroupOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="form-field">
            <label>Độ tin cậy</label>
            <Select v-model="factorForm.confidence_level" :options="confidenceOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="form-field">
          <label>Mô tả yếu tố <span class="req">*</span></label>
          <Textarea v-model="factorForm.factor_text" rows="2" class="w-full" placeholder="Mô tả yếu tố..." />
        </div>
        <div class="form-field checkbox-field">
          <label>
            <input type="checkbox" v-model="factorForm.is_primary" />
            Yếu tố chính (Primary)
          </label>
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showFactorForm = false" />
        <Button label="Thêm" icon="pi pi-plus" @click="submitFactor" :disabled="!factorForm.factor_text" />
      </template>
    </Dialog>
  </div>

  <!-- Loading state — PrimeVue Skeleton -->
  <div v-else-if="store.loading" class="loading-state">
    <div class="skeleton-grid">
      <Skeleton width="10rem" height="1rem" class="mb-3" />
      <Skeleton width="100%" height="5rem" borderRadius="12px" class="mb-4" />
      <Skeleton width="100%" height="2.5rem" borderRadius="8px" class="mb-4" />
      <div class="skeleton-row">
        <Skeleton width="100%" height="14rem" borderRadius="10px" />
        <Skeleton width="360px" height="14rem" borderRadius="10px" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══ Page layout — full-width ═══ */
.case-detail-page { width: 100%; }

/* ═══ Breadcrumb — PrimeVue ═══ */
.case-breadcrumb {
  margin-bottom: 1rem; background: transparent; border: none; padding: 0;
}
:deep(.case-breadcrumb .p-breadcrumb-list) { gap: 0.35rem; }
:deep(.case-breadcrumb .p-menuitem-link) { font-size: 0.85rem; }
:deep(.case-breadcrumb .p-menuitem-text) { font-size: 0.85rem; }

/* ═══ Case Header ═══ */
.case-header {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.header-top {
  display: flex; justify-content: space-between; align-items: flex-start;
  flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;
}
.case-title {
  margin: 0 0 0.5rem; font-size: 1.25rem; font-weight: 700;
  color: var(--p-text-color); line-height: 1.3;
}
.title-sep { color: var(--p-text-muted-color); font-weight: 400; }
.header-tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }

/* ═══ Status Pipeline — PrimeVue Stepper (horizontal) ═══ */
.pipeline-wrap { margin-top: 0.25rem; overflow-x: auto; }
.case-stepper { background: transparent; }
:deep(.case-stepper .p-steplist) { flex-wrap: nowrap; }
:deep(.case-stepper .p-step) { cursor: default; }
:deep(.case-stepper .p-step-header) { cursor: default; }
:deep(.case-stepper .p-step-title) { font-size: 0.78rem; white-space: nowrap; }
/* Separator — the connector line between steps */
:deep(.case-stepper .p-stepper-separator) {
  background: var(--p-surface-300);
  height: 2px;
  flex: 1 1 0;
}
/* Completed steps: green number + active separator */
:deep(.case-stepper .p-step:has(~ .p-step-active) .p-step-number) {
  background: var(--p-green-500); border-color: var(--p-green-500); color: #fff;
}
:deep(.case-stepper .p-step:has(~ .p-step-active) .p-step-title) {
  color: var(--p-green-600); font-weight: 600;
}
:deep(.case-stepper .p-step:has(~ .p-step-active) .p-stepper-separator) {
  background: var(--p-green-500);
}
/* Active step: glow ring */
:deep(.case-stepper .p-step-active .p-step-number) {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--p-primary-color) 20%, transparent);
}
.cancelled-banner {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 1rem; border-radius: 8px;
  background: var(--p-red-50); color: var(--p-red-600);
  font-weight: 600; font-size: 0.85rem; margin-top: 0.5rem;
}

/* ═══ Overview Grid ═══ */
.overview-grid {
  display: grid; grid-template-columns: 1fr 360px; gap: 1.25rem; margin-top: 1rem;
}
.overview-main { display: flex; flex-direction: column; gap: 1rem; }
.overview-side { display: flex; flex-direction: column; gap: 1rem; }

/* ═══ Info Cards ═══ */
.info-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 10px; padding: 1.25rem;
  transition: box-shadow 0.2s;
}
.info-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

/* Card accent variants */
.card-accent-blue   { border-left: 3px solid var(--p-blue-500); }
.card-accent-teal   { border-left: 3px solid var(--p-teal-500); }
.card-accent-orange { border-left: 3px solid var(--p-orange-500); }
.card-accent-purple { border-left: 3px solid var(--p-purple-500); }

.card-header-row {
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.85rem;
}
.card-icon { font-size: 1rem; color: var(--p-text-muted-color); }
.info-card h4 { margin: 0; font-size: 0.9rem; font-weight: 700; }

.info-rows { display: flex; flex-direction: column; }
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.4rem 0; border-bottom: 1px solid var(--p-surface-100);
}
.info-row:last-child { border-bottom: none; }
.info-row label { font-size: 0.8rem; color: var(--p-text-muted-color); font-weight: 600; min-width: 100px; }
.info-row span { font-size: 0.85rem; text-align: right; }
.sla-value { font-weight: 600; color: var(--p-orange-600); }
.mono { font-family: monospace; font-size: 0.8rem; }

.summary-text { font-size: 0.85rem; line-height: 1.6; margin: 0; white-space: pre-wrap; color: var(--p-text-color); }

/* Expert badge — PrimeVue Avatar */
.expert-badge {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.5rem 0;
}
:deep(.expert-avatar) {
  background: var(--p-teal-100); color: var(--p-teal-600);
}
.expert-name { font-size: 0.9rem; font-weight: 600; }

.empty-inline {
  display: flex; align-items: center; gap: 0.5rem;
  color: var(--p-text-muted-color); font-style: italic; font-size: 0.85rem;
  padding: 0.25rem 0;
}

/* RCA stat */
.rca-stat { display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.5rem; }
.rca-stat-num { font-size: 1.75rem; font-weight: 800; color: var(--p-purple-600); line-height: 1; }
.rca-stat-label { font-size: 0.8rem; color: var(--p-text-muted-color); }

/* ═══ RCA Workspace ═══ */
.rca-workspace { margin-top: 1rem; }
.rca-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
.rca-header h3 {
  margin: 0; font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem;
}

/* Empty state */
.empty-state {
  text-align: center; padding: 3rem 1.5rem; color: var(--p-text-muted-color);
}
.empty-icon-wrap {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--p-surface-100);
  display: inline-flex; align-items: center; justify-content: center;
  margin-bottom: 0.75rem;
}
.empty-icon-wrap i { font-size: 1.5rem; }
.empty-state h4 { margin: 0 0 0.25rem; font-size: 1rem; color: var(--p-text-color); }
.empty-state p { margin: 0; font-size: 0.85rem; }

/* RCA card */
.rca-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;
  border-left: 3px solid var(--p-blue-400);
  transition: box-shadow 0.2s;
}
.rca-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.rca-approved { border-left-color: var(--p-green-500); }

.rca-card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;
}
.rca-card-title { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.rca-card-actions { display: flex; gap: 0.35rem; flex-wrap: wrap; }

.rca-body { margin-bottom: 0.75rem; }
.rca-field { margin-bottom: 0.6rem; }
.rca-field label {
  display: block; font-size: 0.72rem; font-weight: 700;
  color: var(--p-text-muted-color); margin-bottom: 0.15rem;
  text-transform: uppercase; letter-spacing: 0.03em;
}
.rca-field p { margin: 0; font-size: 0.85rem; line-height: 1.5; }

.rca-causes-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem 1.5rem; margin: 0.75rem 0; }

.factors-section { border-top: 1px solid var(--p-surface-border); padding-top: 1rem; margin-top: 1rem; }
.factors-section h5 {
  margin: 0 0 0.65rem; font-size: 0.85rem;
  display: flex; align-items: center; gap: 0.4rem;
}
.factor-table { font-size: 0.85rem; }

.rca-meta {
  display: flex; gap: 1.25rem; flex-wrap: wrap;
  font-size: 0.75rem; color: var(--p-text-muted-color); margin-top: 0.75rem;
  padding-top: 0.5rem; border-top: 1px dashed var(--p-surface-200);
}
.rca-meta i { margin-right: 0.25rem; }

/* ═══ Timeline — PrimeVue ═══ */
.timeline-section { margin-top: 1rem; }
.timeline-section h3 {
  margin: 0 0 1.25rem; font-size: 1.05rem;
  display: flex; align-items: center; gap: 0.5rem;
}
.case-timeline { padding: 0; }
:deep(.case-timeline .p-timeline-event-opposite) { min-width: 120px; max-width: 160px; flex: none; }
:deep(.case-timeline .p-timeline-event-connector) { background: var(--p-surface-200); }
.tl-marker {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--p-surface-card);
  border: 2px solid var(--p-surface-300);
  display: flex; align-items: center; justify-content: center;
}
.tl-marker i { font-size: 0.85rem; }
.tl-card {
  background: var(--p-surface-card); border: 1px solid var(--p-surface-border);
  border-radius: 8px; padding: 0.75rem 1rem;
  transition: box-shadow 0.15s;
}
.tl-card:hover { box-shadow: 0 1px 6px rgba(0,0,0,0.05); }
.tl-time { font-size: 0.72rem; color: var(--p-text-muted-color); font-weight: 500; text-align: right; }
.tl-detail { font-size: 0.85rem; line-height: 1.4; }

/* ═══ Forms & Dialogs ═══ */
.form-grid { display: flex; flex-direction: column; gap: 0.85rem; }
.rca-form-grid { display: flex; flex-direction: column; gap: 0.85rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.form-field { display: flex; flex-direction: column; gap: 0.35rem; }
.form-field label { font-weight: 600; font-size: 0.85rem; }
.checkbox-field label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.req { color: var(--p-red-500); }
.w-full { width: 100%; }

/* ═══ Loading — PrimeVue Skeleton ═══ */
.loading-state { padding: 1.5rem; }
.skeleton-grid { display: flex; flex-direction: column; gap: 0; }
.skeleton-row { display: flex; gap: 1.25rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }

/* ═══ Responsive Dialog Classes ═══ */
:deep(.responsive-dialog) { width: 90vw !important; }
:deep(.dialog-sm) { max-width: 460px !important; }
:deep(.dialog-md) { max-width: 540px !important; }
:deep(.dialog-lg) { max-width: 740px !important; }

/* ═══ Responsive — Tablet ═══ */
@media (max-width: 1024px) {
  .overview-grid { grid-template-columns: 1fr; }
  .overview-side { flex-direction: row; flex-wrap: wrap; }
  .overview-side .info-card { flex: 1 1 250px; }
  :deep(.case-stepper .p-step-title) { font-size: 0.7rem; }
  .skeleton-row { flex-direction: column; }
  .skeleton-row :deep(.p-skeleton) { width: 100% !important; }
}

/* ═══ Responsive — Mobile ═══ */
@media (max-width: 768px) {
  .header-top { flex-direction: column; }
  .header-actions { width: 100%; }
  .case-title { font-size: 1.05rem; }
  .pipeline-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  :deep(.case-stepper .p-step-title) { display: none; }
  .rca-causes-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .rca-card-header { flex-direction: column; align-items: flex-start; }
  .rca-card-actions { width: 100%; justify-content: flex-start; }
  .overview-side { flex-direction: column; }
  .overview-side .info-card { flex: 1 1 auto; }
  .tl-card { padding: 0.6rem 0.75rem; }
  :deep(.case-timeline .p-timeline-event-opposite) { min-width: 80px; max-width: 100px; }
  .tl-time { font-size: 0.68rem; }
}

/* ═══ Responsive — Small Mobile ═══ */
@media (max-width: 480px) {
  .case-header { padding: 1rem; border-radius: 8px; }
  .info-card { padding: 1rem; border-radius: 8px; }
  .rca-card { padding: 1rem; }
  .header-actions { flex-direction: column; }
  .header-actions :deep(.p-button) { width: 100%; }
  :deep(.case-breadcrumb .p-menuitem-text) { font-size: 0.78rem; }
}
</style>
