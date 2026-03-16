<script setup>
import Tag from 'primevue/tag'
import { computed } from 'vue'

const props = defineProps({
  value: { type: String, required: true },
})

const config = {
  P0: { label: 'P0 — Khẩn', severity: 'danger' },
  P1: { label: 'P1 — Cao', severity: 'danger' },
  P2: { label: 'P2 — Vừa', severity: 'warn' },
  P3: { label: 'P3 — Thấp', severity: 'info' },
}

const item = computed(() => config[props.value] || { label: props.value, severity: 'secondary' })
</script>

<template>
  <Tag :value="item.label" :severity="item.severity" rounded />
</template>
