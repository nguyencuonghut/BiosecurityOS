<script setup>
/**
 * FloorplanCanvas.vue — Interactive floorplan with marker overlay and scar dots.
 *
 * Props:
 *   markers    — Array of { id, marker_type, label, x_percent, y_percent }
 *   scars      — Array of { id, scar_type, title, confidence_level, x_percent, y_percent }
 *   readonly   — Boolean, if true hide click-to-add
 *
 * Emits:
 *   markerClick(marker) — when a marker is clicked
 *   scarClick(scar)     — when a scar dot is clicked
 *   canvasClick({ x_percent, y_percent }) — for adding markers
 */

import { ref, computed } from 'vue'

const props = defineProps({
  markers: { type: Array, default: () => [] },
  scars: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: true },
})

const emit = defineEmits(['markerClick', 'scarClick', 'canvasClick'])

const hoveredMarker = ref(null)
const hoveredScar = ref(null)

// ── Marker icon mapping ───────────────────────────────────────
const markerIcons = {
  gate: 'pi-sign-in',
  disinfection: 'pi-sparkles',
  feed_storage: 'pi-box',
  quarantine: 'pi-shield',
  dead_pig_zone: 'pi-times-circle',
  checkpoint: 'pi-verified',
}

function getMarkerIcon(type) {
  return markerIcons[type] || 'pi-map-marker'
}

// ── Scar color mapping ────────────────────────────────────────
const scarColors = {
  outbreak: '#ef4444',       // red
  hotspot: '#f97316',        // orange
  repeated_breach: '#eab308', // yellow
  near_miss: '#3b82f6',     // blue
  structural_flaw: '#8b5cf6', // purple
}

const scarTypeLabels = {
  outbreak: 'Ổ dịch',
  hotspot: 'Hotspot',
  repeated_breach: 'Vi phạm lặp lại',
  near_miss: 'Suýt xảy ra',
  structural_flaw: 'Lỗi cấu trúc',
}

function getScarColor(type) {
  return scarColors[type] || '#6b7280'
}

function confidenceOpacity(level) {
  return { confirmed: 1, probable: 0.75, suspected: 0.5 }[level] || 0.6
}

// ── Canvas click handler ──────────────────────────────────────
function onCanvasClick(event) {
  if (props.readonly) return
  const rect = event.currentTarget.getBoundingClientRect()
  const x_percent = ((event.clientX - rect.left) / rect.width) * 100
  const y_percent = ((event.clientY - rect.top) / rect.height) * 100
  emit('canvasClick', {
    x_percent: Math.round(x_percent * 10) / 10,
    y_percent: Math.round(y_percent * 10) / 10,
  })
}

// ── Legend items ──────────────────────────────────────────────
const legendItems = computed(() =>
  Object.entries(scarColors).map(([type, color]) => ({ type, color, label: scarTypeLabels[type] }))
)
</script>

<template>
  <div class="floorplan-canvas">
    <!-- Canvas area with grey background acting as a schematic grid -->
    <div class="canvas-area" @click="onCanvasClick">
      <!-- Grid pattern background -->
      <svg class="grid-bg" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="var(--p-surface-300)" stroke-width="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <!-- Markers -->
      <div
        v-for="m in markers"
        :key="'m-' + m.id"
        class="marker-pin"
        :style="{ left: m.x_percent + '%', top: m.y_percent + '%' }"
        @click.stop="emit('markerClick', m)"
        @mouseenter="hoveredMarker = m.id"
        @mouseleave="hoveredMarker = null"
      >
        <i :class="'pi ' + getMarkerIcon(m.marker_type)" />
        <!-- Tooltip -->
        <div class="marker-tooltip" v-if="hoveredMarker === m.id">
          <div class="tooltip-title">{{ m.label }}</div>
          <div class="tooltip-sub">{{ m.marker_type }}</div>
        </div>
      </div>

      <!-- Scar dots -->
      <div
        v-for="s in scars"
        :key="'s-' + s.id"
        class="scar-dot"
        :class="{ 'scar-pulse': s.confidence_level !== 'confirmed' }"
        :style="{
          left: (s.x_percent ?? 50) + '%',
          top: (s.y_percent ?? 50) + '%',
          '--scar-color': getScarColor(s.scar_type),
          opacity: confidenceOpacity(s.confidence_level),
        }"
        @click.stop="emit('scarClick', s)"
        @mouseenter="hoveredScar = s.id"
        @mouseleave="hoveredScar = null"
      >
        <div class="scar-tooltip" v-if="hoveredScar === s.id">
          <div class="tooltip-title">{{ s.title }}</div>
          <div class="tooltip-sub">{{ scarTypeLabels[s.scar_type] || s.scar_type }} · {{ s.confidence_level }}</div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="canvas-legend" v-if="scars.length > 0 || markers.length > 0">
      <div class="legend-section" v-if="scars.length > 0">
        <span class="legend-title">Loại scar:</span>
        <span v-for="item in legendItems" :key="item.type" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
      </div>
      <div class="legend-section" v-if="markers.length > 0">
        <span class="legend-title">Markers: {{ markers.length }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.floorplan-canvas {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.canvas-area {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  background: var(--p-surface-100);
  border: 1px solid var(--p-surface-300);
  border-radius: var(--p-border-radius);
  overflow: hidden;
  cursor: default;
}
.grid-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* ── Marker pins ─────────────────────────────────────── */
.marker-pin {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--p-primary-color);
  color: var(--p-primary-contrast-color);
  border-radius: 50%;
  font-size: 0.75rem;
  cursor: pointer;
  z-index: 2;
  transition: transform 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
}
.marker-pin:hover {
  transform: translate(-50%, -50%) scale(1.2);
  z-index: 10;
}

/* ── Scar dots ───────────────────────────────────────── */
.scar-dot {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 18px;
  background: var(--scar-color, #ef4444);
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  z-index: 3;
  transition: transform 0.15s;
  box-shadow: 0 0 6px rgba(0,0,0,0.3);
}
.scar-dot:hover {
  transform: translate(-50%, -50%) scale(1.4);
  z-index: 10;
}

/* Pulsing animation for non-confirmed scars */
.scar-pulse {
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 6px rgba(0,0,0,0.3); }
  50% { box-shadow: 0 0 12px 4px var(--scar-color); }
}

/* ── Tooltips ────────────────────────────────────────── */
.marker-tooltip,
.scar-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--p-surface-900);
  color: var(--p-surface-0);
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  white-space: nowrap;
  font-size: 0.75rem;
  pointer-events: none;
  z-index: 20;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.tooltip-title {
  font-weight: 600;
}
.tooltip-sub {
  opacity: 0.8;
  font-size: 0.7rem;
}

/* ── Legend ───────────────────────────────────────────── */
.canvas-legend {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}
.legend-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.legend-title {
  font-weight: 600;
  color: var(--p-text-color);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
</style>
