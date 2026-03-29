<script setup>
/**
 * FarmLessonPanel.vue — Lessons tab inside FarmDetailView.
 *
 * Shows lessons applicable to this farm by searching similar lessons
 * based on the farm's farm_type and ownership_type.
 */

import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LessonDetailDrawer from '@/components/lessons/LessonDetailDrawer.vue'
import * as lessonService from '@/services/lessonService.js'

const props = defineProps({
  farmId: { type: String, required: true },
  farmType: { type: String, default: null },
  ownershipType: { type: String, default: null },
})

const emit = defineEmits(['loaded'])

const toast = useToast()
const lessons = ref([])
const total = ref(0)
const loading = ref(false)
const drawerVisible = ref(false)
const selectedLessonId = ref(null)

onMounted(() => {
  loadLessons()
})

async function loadLessons() {
  loading.value = true
  try {
    const params = { page_size: 50 }
    if (props.farmType) params.farm_type = props.farmType

    const result = await lessonService.searchSimilar(params)
    lessons.value = result.data || []
    total.value = result.meta?.total || 0
    emit('loaded', total.value)
  } catch {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: 'Không thể tải bài học', life: 3000 })
  } finally {
    loading.value = false
  }
}

function onRowSelect(event) {
  selectedLessonId.value = event.data.id
  drawerVisible.value = true
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
  <div class="farm-lesson-panel">
    <DataTable
      :value="lessons"
      :loading="loading"
      stripedRows
      size="small"
      selectionMode="single"
      @rowSelect="onRowSelect"
      :paginator="false"
      scrollable
      scrollHeight="400px"
    >
      <template #empty>Chưa có bài học nào áp dụng cho trại này.</template>
      <Column field="lesson_no" header="Mã" style="width: 140px">
        <template #body="{ data }">
          <span style="font-family: monospace; font-size: 0.8rem; color: var(--p-text-muted-color)">{{ data.lesson_no }}</span>
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

    <LessonDetailDrawer
      v-model:visible="drawerVisible"
      :lessonId="selectedLessonId"
    />
  </div>
</template>
