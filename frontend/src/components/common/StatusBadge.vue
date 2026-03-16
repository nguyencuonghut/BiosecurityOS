<script setup>
import Tag from 'primevue/tag'
import { computed } from 'vue'

const props = defineProps({
  value: { type: String, required: true },
  type: { type: String, default: 'status' }, // status | risk | confidence | clean_dirty
})

const severityMap = {
  status: {
    active: 'success',
    paused: 'warn',
    closed: 'danger',
    archived: 'secondary',
    locked: 'danger',
    inactive: 'secondary',
    draft: 'secondary',
    submitted: 'info',
    reviewed: 'success',
    open: 'warn',
  },
  risk: {
    low: 'success',
    medium: 'warn',
    high: 'danger',
    critical: 'danger',
  },
  confidence: {
    suspected: 'warn',
    probable: 'info',
    confirmed: 'success',
  },
  clean_dirty: {
    clean: 'success',
    buffer: 'warn',
    dirty: 'danger',
  },
}

const labelMap = {
  status: {
    active: 'Hoạt động',
    paused: 'Tạm dừng',
    closed: 'Đã đóng',
    archived: 'Lưu trữ',
    locked: 'Khóa',
    inactive: 'Ngừng',
    draft: 'Nháp',
    submitted: 'Đã nộp',
    reviewed: 'Đã duyệt',
    open: 'Mở',
  },
  risk: {
    low: 'Thấp',
    medium: 'Trung bình',
    high: 'Cao',
    critical: 'Nghiêm trọng',
  },
  confidence: {
    suspected: 'Nghi ngờ',
    probable: 'Có thể',
    confirmed: 'Xác nhận',
  },
  clean_dirty: {
    clean: 'Sạch',
    buffer: 'Đệm',
    dirty: 'Bẩn',
  },
}

const severity = computed(() => severityMap[props.type]?.[props.value] || 'secondary')
const label = computed(() => labelMap[props.type]?.[props.value] || props.value)
</script>

<template>
  <Tag :value="label" :severity="severity" rounded />
</template>
