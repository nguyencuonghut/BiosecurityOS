<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useScorecardStore } from '@/stores/scorecard.js'
import { useKillerMetricStore } from '@/stores/killerMetric.js'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import Popover from 'primevue/popover'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Panel from 'primevue/panel'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import * as scorecardService from '@/services/scorecardService.js'

const route = useRoute()
const router = useRouter()
const store = useScorecardStore()
const kmStore = useKillerMetricStore()
const toast = useToast()
const confirm = useConfirm()

const templateId = computed(() => route.params.id)
const isDraft = computed(() => store.currentTemplate?.status === 'draft')

const sectionTypeOptions = [
  { label: 'Hạ tầng', value: 'hardware' },
  { label: 'Quy trình', value: 'software' },
  { label: 'Hành vi', value: 'behavior' },
  { label: 'Giám sát', value: 'monitoring' },
  { label: 'Khác', value: 'other' },
]

const responseTypeOptions = [
  { label: 'Có / Không', value: 'yes_no' },
  { label: 'Điểm 0-5', value: 'score_0_5' },
  { label: 'Tùy chọn', value: 'option' },
  { label: 'Số', value: 'numeric' },
  { label: 'Tự do', value: 'text' },
]

// ── Section dialog ──
const showSectionDialog = ref(false)
const editingSectionId = ref(null)
const sectionForm = ref({ code: '', name: '', section_type: null, weight: 0, display_order: 1 })

// ── Item dialog ──
const showItemDialog = ref(false)
const activeSection = ref(null)
const editingItemId = ref(null)
const itemForm = ref({
  code: '', question_text: '', response_type: null, max_score: 5,
  weight: 1, killer_metric_definition_id: null, threshold_warning: null,
  threshold_fail: null, guidance_text: '', display_order: 1,
})

onMounted(async () => {
  await store.fetchTemplate(templateId.value)
  await kmStore.fetchDefinitions()
})

// ── Template actions ──
async function handleActivate() {
  try {
    await store.activateTemplate(templateId.value)
    toast.add({ severity: 'success', summary: 'Đã kích hoạt', life: 3000 })
    await store.fetchTemplate(templateId.value)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Lỗi kích hoạt', life: 5000 })
  }
}

async function handleArchive() {
  try {
    await store.archiveTemplate(templateId.value)
    toast.add({ severity: 'warn', summary: 'Đã lưu trữ', life: 3000 })
    await store.fetchTemplate(templateId.value)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Lỗi lưu trữ', life: 5000 })
  }
}

// ── Section CRUD ──
function openAddSection() {
  editingSectionId.value = null
  sectionForm.value = { code: '', name: '', section_type: null, weight: 0, display_order: store.sections.length + 1 }
  showSectionDialog.value = true
}

function openEditSection(section) {
  editingSectionId.value = section.id
  sectionForm.value = { code: section.code, name: section.name, section_type: section.section_type, weight: Number(section.weight), display_order: section.display_order }
  showSectionDialog.value = true
}

async function handleSaveSection() {
  try {
    await store.saveSection(templateId.value, sectionForm.value, editingSectionId.value)
    showSectionDialog.value = false
    await store.fetchTemplate(templateId.value)
    toast.add({ severity: 'success', summary: 'Đã lưu section', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Lỗi lưu section', life: 5000 })
  }
}

// ── Item CRUD ──
function openAddItem(section) {
  activeSection.value = section
  editingItemId.value = null
  itemForm.value = {
    code: '', question_text: '', response_type: null, max_score: 5,
    weight: 1, killer_metric_definition_id: null, threshold_warning: null,
    threshold_fail: null, guidance_text: '', display_order: (section.items?.length || 0) + 1,
  }
  showItemDialog.value = true
}

function openEditItem(section, item) {
  activeSection.value = section
  editingItemId.value = item.id
  itemForm.value = {
    code: item.code, question_text: item.question_text, response_type: item.response_type,
    max_score: Number(item.max_score), weight: Number(item.weight),
    killer_metric_definition_id: item.killer_metric_definition_id || null,
    threshold_warning: item.threshold_warning != null ? Number(item.threshold_warning) : null,
    threshold_fail: item.threshold_fail != null ? Number(item.threshold_fail) : null,
    guidance_text: item.guidance_text || '', display_order: item.display_order,
  }
  showItemDialog.value = true
}

async function handleSaveItem() {
  try {
    await store.saveItem(activeSection.value.id, itemForm.value, editingItemId.value)
    showItemDialog.value = false
    await store.fetchTemplate(templateId.value)
    toast.add({ severity: 'success', summary: 'Đã lưu item', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e.response?.data?.error?.message || 'Lỗi lưu item', life: 5000 })
  }
}

function confirmDeleteItem(section, item) {
  confirm.require({
    message: `Xóa item "${item.code}" ?`,
    header: 'Xác nhận xóa',
    icon: 'pi pi-trash',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await store.removeItem(section.id, item.id)
        await store.fetchTemplate(templateId.value)
        toast.add({ severity: 'info', summary: 'Đã xóa', life: 3000 })
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể xóa item', life: 5000 })
      }
    },
  })
}

function sectionTypeLabel(val) {
  return sectionTypeOptions.find((o) => o.value === val)?.label || val
}

function responseTypeLabel(val) {
  return responseTypeOptions.find((o) => o.value === val)?.label || val
}

function kmDefCode(id) {
  return kmStore.definitions.find((d) => d.id === id)?.code || ''
}
function kmDefName(id) {
  return kmStore.definitions.find((d) => d.id === id)?.name || ''
}

// ── Killer definition popover ──
const killerPopover = ref()
const activeKmDef = ref(null)
function showKillerPopover(event, definitionId) {
  activeKmDef.value = kmStore.definitions.find((d) => d.id === definitionId) || null
  killerPopover.value.toggle(event)
}

async function handleClone() {
  try {
    const src = store.currentTemplate
    const cloned = await scorecardService.createTemplate({
      code: src.code + '-COPY',
      name: src.name + ' (Clone)',
      farm_type: src.farm_type,
      ownership_type: src.ownership_type,
      risk_profile: src.risk_profile,
      version_no: (src.version_no || 1) + 1,
      effective_from: null,
      effective_to: null,
    })
    // Clone sections and items
    for (const section of store.sections) {
      const newSection = await scorecardService.createSection(cloned.id, {
        code: section.code,
        name: section.name,
        section_type: section.section_type,
        weight: Number(section.weight),
        display_order: section.display_order,
      })
      for (const item of section.items || []) {
        await scorecardService.createItem(newSection.id, {
          code: item.code,
          question_text: item.question_text,
          response_type: item.response_type,
          max_score: Number(item.max_score),
          weight: Number(item.weight),
          killer_metric_definition_id: item.killer_metric_definition_id || null,
          threshold_warning: item.threshold_warning != null ? Number(item.threshold_warning) : null,
          threshold_fail: item.threshold_fail != null ? Number(item.threshold_fail) : null,
          guidance_text: item.guidance_text || '',
          display_order: item.display_order,
        })
      }
    }
    toast.add({ severity: 'success', summary: 'Đã clone template', life: 3000 })
    router.push(`/scorecards/${cloned.id}`)
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi clone', detail: e.response?.data?.error?.message || 'Không thể clone', life: 5000 })
  }
}
</script>

<template>
  <div v-if="store.currentTemplate" class="scorecard-builder">
    <!-- Header -->
    <div class="builder-header">
      <div>
        <Button icon="pi pi-arrow-left" text rounded @click="router.push('/scorecards')" />
        <h2 class="inline">{{ store.currentTemplate.code }} — {{ store.currentTemplate.name }}</h2>
      </div>
      <div class="header-actions">
        <StatusBadge :value="store.currentTemplate.status" />
        <span class="version-tag">v{{ store.currentTemplate.version_no }}</span>
        <Button v-if="isDraft" label="Kích hoạt" icon="pi pi-check-circle" severity="success" size="small" @click="handleActivate" />
        <Button v-if="store.currentTemplate.status !== 'archived'" label="Lưu trữ" icon="pi pi-inbox" severity="warn" size="small" @click="handleArchive" />
        <Button label="Clone" icon="pi pi-copy" severity="secondary" size="small" @click="handleClone" />
      </div>
    </div>

    <!-- Sections -->
    <div class="sections-area">
      <div class="section-toolbar">
        <h3>Các phần đánh giá ({{ store.sections.length }})</h3>
        <Button v-if="isDraft" label="Thêm phần" icon="pi pi-plus" size="small" @click="openAddSection" />
      </div>

      <Panel v-for="section in store.sections" :key="section.id" :header="section.name" toggleable class="section-panel">
        <template #header>
          <div class="section-header-content">
            <span class="section-title">
              <Tag :value="sectionTypeLabel(section.section_type)" severity="info" rounded />
              {{ section.code }} — {{ section.name }}
            </span>
            <span class="section-meta">
              Trọng số: <strong>{{ section.weight }}</strong>
              &nbsp;|&nbsp; {{ section.items?.length || 0 }} items
            </span>
          </div>
        </template>
        <template #icons>
          <Button v-if="isDraft" icon="pi pi-pencil" text rounded size="small" @click.stop="openEditSection(section)" />
        </template>

        <DataTable :value="section.items || []" size="small" stripedRows>
          <Column field="display_order" header="#" style="width: 3rem" />
          <Column field="code" header="Mã" style="width: 8rem" />
          <Column field="question_text" header="Câu hỏi" />
          <Column field="response_type" header="Loại" style="width: 8rem">
            <template #body="{ data }">{{ responseTypeLabel(data.response_type) }}</template>
          </Column>
          <Column field="max_score" header="Max" style="width: 4rem" />
          <Column field="weight" header="Wt" style="width: 4rem" />
          <Column header="Killer" style="width: 10rem">
            <template #body="{ data }">
              <button
                v-if="data.is_killer_related && data.killer_metric_definition_id"
                class="killer-link"
                @click="showKillerPopover($event, data.killer_metric_definition_id)"
              >
                <i class="pi pi-exclamation-triangle" />
                {{ kmDefCode(data.killer_metric_definition_id) }}
              </button>
            </template>
          </Column>
          <Column v-if="isDraft" header="" style="width: 6rem">
            <template #body="{ data }">
              <Button icon="pi pi-pencil" text rounded size="small" @click="openEditItem(section, data)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="confirmDeleteItem(section, data)" />
            </template>
          </Column>
        </DataTable>

        <div v-if="isDraft" class="mt-2">
          <Button label="Thêm item" icon="pi pi-plus" text size="small" @click="openAddItem(section)" />
        </div>
      </Panel>
    </div>

    <!-- Section Dialog -->
    <Dialog v-model:visible="showSectionDialog" :header="editingSectionId ? 'Sửa phần' : 'Thêm phần'" :modal="true" style="width: 28rem">
      <div class="dialog-form">
        <div class="field">
          <label>Mã *</label>
          <InputText v-model="sectionForm.code" class="w-full" />
        </div>
        <div class="field">
          <label>Tên *</label>
          <InputText v-model="sectionForm.name" class="w-full" />
        </div>
        <div class="field">
          <label>Loại *</label>
          <Select v-model="sectionForm.section_type" :options="sectionTypeOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Trọng số *</label>
            <InputNumber v-model="sectionForm.weight" :min="0" :max="1" :minFractionDigits="2" :maxFractionDigits="2" class="w-full" />
          </div>
          <div class="field">
            <label>Thứ tự</label>
            <InputNumber v-model="sectionForm.display_order" :min="1" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" text @click="showSectionDialog = false" />
        <Button label="Lưu" icon="pi pi-check" @click="handleSaveSection" />
      </template>
    </Dialog>

    <!-- Item Dialog -->
    <Dialog v-model:visible="showItemDialog" :header="editingItemId ? 'Sửa item' : 'Thêm item'" :modal="true" style="width: 36rem">
      <div class="dialog-form">
        <div class="field-row">
          <div class="field">
            <label>Mã *</label>
            <InputText v-model="itemForm.code" class="w-full" />
          </div>
          <div class="field">
            <label>Loại phản hồi *</label>
            <Select v-model="itemForm.response_type" :options="responseTypeOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="field">
          <label>Câu hỏi / Tiêu chí *</label>
          <Textarea v-model="itemForm.question_text" rows="2" class="w-full" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Điểm tối đa *</label>
            <InputNumber v-model="itemForm.max_score" :min="0" class="w-full" />
          </div>
          <div class="field">
            <label>Trọng số *</label>
            <InputNumber v-model="itemForm.weight" :min="0" :minFractionDigits="2" :maxFractionDigits="2" class="w-full" />
          </div>
          <div class="field">
            <label>Thứ tự</label>
            <InputNumber v-model="itemForm.display_order" :min="1" class="w-full" />
          </div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Ngưỡng cảnh báo</label>
            <InputNumber v-model="itemForm.threshold_warning" :min="0" class="w-full" />
          </div>
          <div class="field">
            <label>Ngưỡng lỗi</label>
            <InputNumber v-model="itemForm.threshold_fail" :min="0" class="w-full" />
          </div>
        </div>
        <div class="field">
          <label>Hướng dẫn chấm</label>
          <Textarea v-model="itemForm.guidance_text" rows="2" class="w-full" />
        </div>
        <div class="field">
          <label>Killer Metric liên kết</label>
          <Select
            v-model="itemForm.killer_metric_definition_id"
            :options="kmStore.definitions"
            optionLabel="name"
            optionValue="id"
            placeholder="Không liên kết"
            showClear
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Hủy" text @click="showItemDialog = false" />
        <Button label="Lưu" icon="pi pi-check" @click="handleSaveItem" />
      </template>
    </Dialog>
  </div>
  <div v-else class="loading-container">
    <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
  </div>

  <!-- Killer Definition Popover -->
  <Popover ref="killerPopover">
    <div v-if="activeKmDef" class="km-popover">
      <div class="km-popover-title">
        <i class="pi pi-exclamation-triangle" style="color: var(--p-red-500)" />
        <strong>{{ activeKmDef.code }}</strong>
      </div>
      <p class="km-popover-name">{{ activeKmDef.name }}</p>
      <div class="km-popover-row" v-if="activeKmDef.description">
        <span class="km-popover-label">Mô tả</span>
        <span>{{ activeKmDef.description }}</span>
      </div>
      <div class="km-popover-row">
        <span class="km-popover-label">Mức độ</span>
        <Tag :value="activeKmDef.severity_level" :severity="activeKmDef.severity_level === 'critical' ? 'danger' : activeKmDef.severity_level === 'high' ? 'warn' : 'info'" />
      </div>
      <div class="km-popover-row">
        <span class="km-popover-label">Nguồn</span>
        <span>{{ { scorecard_item: 'Scorecard', field_report: 'Báo cáo', both: 'Cả hai' }[activeKmDef.source_type] || activeKmDef.source_type }}</span>
      </div>
    </div>
  </Popover>
</template>

<style scoped>
.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.builder-header h2 { margin: 0; color: var(--p-text-color); }
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.inline { display: inline; margin-left: 0.5rem; }
.version-tag {
  background: var(--p-primary-color);
  color: var(--p-primary-contrast-color);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}
.sections-area { display: flex; flex-direction: column; gap: 0.75rem; }
.sections-area h3 { color: var(--p-text-color); }
.section-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-panel { margin-bottom: 0.5rem; }
.section-header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  width: 100%;
}
.section-title { display: flex; align-items: center; gap: 0.5rem; font-weight: 600; }
.section-meta { font-size: 0.8rem; color: var(--p-text-muted-color); margin-left: auto; }
.dialog-form { display: flex; flex-direction: column; gap: 0.875rem; }
.field { display: flex; flex-direction: column; gap: 0.375rem; flex: 1; }
.field label { font-weight: 600; font-size: 0.875rem; }
.field-row { display: flex; gap: 0.75rem; }
.mt-2 { margin-top: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }
.loading-container { display: flex; justify-content: center; padding: 4rem; }
.killer-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--p-red-500);
  font-size: 0.8rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}
.killer-link:hover { text-decoration: underline; }
.km-popover { display: flex; flex-direction: column; gap: 0.5rem; min-width: 220px; max-width: 300px; }
.km-popover-title { display: flex; align-items: center; gap: 0.4rem; font-size: 1rem; }
.km-popover-name { margin: 0; font-size: 0.9rem; color: var(--p-text-color); }
.km-popover-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; }
.km-popover-label { font-weight: 600; color: var(--p-text-muted-color); min-width: 52px; }
</style>
