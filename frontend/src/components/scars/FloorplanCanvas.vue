<script setup>
/**
 * FloorplanCanvas.vue — Interactive floorplan with marker overlay, scar dots and route arrows.
 *
 * Props:
 *   markers    — Array of { id, marker_type, label, x_percent, y_percent, area_id }
 *   scars      — Array of { id, scar_type, title, confidence_level, x_percent, y_percent }
 *   routes     — Array of { id, from_area_id, to_area_id, route_type, direction_rule }
 *   readonly   — Boolean, if true hide click-to-add
 *   imageUrl   — Background floorplan image URL
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
  routes: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: true },
  imageUrl: { type: String, default: null },
})

const emit = defineEmits(['markerClick', 'scarClick', 'canvasClick', 'markerDragEnd'])

const hoveredMarker = ref(null)
const hoveredScar = ref(null)
const imageRef = ref(null)
const canvasAspect = ref('16 / 10')  // default, updated on image load

function onImageLoad() {
  const img = imageRef.value
  if (img && img.naturalWidth && img.naturalHeight) {
    canvasAspect.value = `${img.naturalWidth} / ${img.naturalHeight}`
  }
}

// ── Drag state ────────────────────────────────────────────────
const draggingMarker = ref(null)
const dragOffset = ref({ x: 0, y: 0 })
const canvasRef = ref(null)
const didDrag = ref(false)

function getContentOrigin(el) {
  const rect = el.getBoundingClientRect()
  const style = getComputedStyle(el)
  return {
    x: rect.left + (parseFloat(style.borderLeftWidth) || 0),
    y: rect.top + (parseFloat(style.borderTopWidth) || 0),
    w: el.clientWidth,
    h: el.clientHeight,
  }
}

function onMarkerPointerDown(event, marker) {
  if (props.readonly) return
  event.preventDefault()
  event.stopPropagation()
  didDrag.value = false
  draggingMarker.value = { ...marker }
  const c = getContentOrigin(canvasRef.value)
  dragOffset.value = {
    x: event.clientX - (marker.x_percent / 100) * c.w - c.x,
    y: event.clientY - (marker.y_percent / 100) * c.h - c.y,
  }
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(event) {
  if (!draggingMarker.value || !canvasRef.value) return
  didDrag.value = true
  const c = getContentOrigin(canvasRef.value)
  let x = ((event.clientX - c.x - dragOffset.value.x) / c.w) * 100
  let y = ((event.clientY - c.y - dragOffset.value.y) / c.h) * 100
  x = Math.max(0, Math.min(100, x))
  y = Math.max(0, Math.min(100, y))
  draggingMarker.value.x_percent = Math.round(x * 10) / 10
  draggingMarker.value.y_percent = Math.round(y * 10) / 10
}

function onPointerUp() {
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
  if (!draggingMarker.value) return
  if (didDrag.value) {
    const orig = props.markers.find(m => m.id === draggingMarker.value.id)
    if (orig && (orig.x_percent !== draggingMarker.value.x_percent || orig.y_percent !== draggingMarker.value.y_percent)) {
      emit('markerDragEnd', {
        id: draggingMarker.value.id,
        x_percent: draggingMarker.value.x_percent,
        y_percent: draggingMarker.value.y_percent,
      })
    }
  }
  draggingMarker.value = null
}

function onMarkerClicked(event, marker) {
  if (didDrag.value) {
    // Was a drag, don't treat as click
    didDrag.value = false
    return
  }
  emit('markerClick', marker)
}

// ── Canvas click handler ──────────────────────────────────────
function onCanvasClick(event) {
  if (props.readonly) return
  const c = getContentOrigin(event.currentTarget)
  const x_percent = ((event.clientX - c.x) / c.w) * 100
  const y_percent = ((event.clientY - c.y) / c.h) * 100
  emit('canvasClick', {
    x_percent: Math.round(x_percent * 10) / 10,
    y_percent: Math.round(y_percent * 10) / 10,
  })
}

function displayX(m) {
  if (draggingMarker.value && draggingMarker.value.id === m.id) return draggingMarker.value.x_percent
  return m.x_percent
}
function displayY(m) {
  if (draggingMarker.value && draggingMarker.value.id === m.id) return draggingMarker.value.y_percent
  return m.y_percent
}

// ── Marker icon & color mapping (biosecurity context) ─────────
// Keys = area_type from DB: gate, production, buffer, logistics,
//         office, quarantine, buffer_zone, storage, yard
// Uses MDI (Material Design Icons) for industry-specific icons
const markerConfig = {
  gate:        { icon: 'mdi-gate',                    color: '#64748b', label: 'Cổng' },
  production:  { icon: 'mdi-pig-variant-outline',     color: '#22c55e', label: 'Khu sạch' },
  buffer:      { icon: 'mdi-shield-half-full',        color: '#f59e0b', label: 'Khu đệm' },
  logistics:   { icon: 'mdi-virus',                   color: '#ef4444', label: 'Khu bẩn' },
  office:      { icon: 'mdi-office-building-outline', color: '#6366f1', label: 'Văn phòng' },
  quarantine:  { icon: 'mdi-shield-alert-outline',    color: '#dc2626', label: 'Cách ly' },
  buffer_zone: { icon: 'mdi-shower-head',             color: '#0ea5e9', label: 'Sát trùng' },
  storage:     { icon: 'mdi-warehouse',               color: '#a855f7', label: 'Kho cám' },
  yard:        { icon: 'mdi-skull-outline',           color: '#78716c', label: 'Xử lý xác' },
}

function getMarkerIcon(type) {
  return markerConfig[type]?.icon || 'mdi-map-marker'
}

function getMarkerColor(type) {
  return markerConfig[type]?.color || '#6b7280'
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

// ── Legend items ──────────────────────────────────────────────
const legendItems = computed(() =>
  Object.entries(scarColors).map(([type, color]) => ({ type, color, label: scarTypeLabels[type] }))
)

// ── Route arrow lines ─────────────────────────────────────────
const routeColors = {
  person: '#3b82f6',    // blue
  vehicle: '#f97316',   // orange
  deadstock: '#ef4444', // red
  feed: '#22c55e',      // green
}

const routeTypeLabels = {
  person: 'Người',
  vehicle: 'Xe',
  deadstock: 'Xác chết',
  feed: 'Cám',
}

// Build marker lookup by area_id for route drawing
const areaMarkerMap = computed(() => {
  const map = {}
  for (const m of props.markers) {
    if (m.area_id) map[m.area_id] = m
  }
  return map
})

// Compute route lines with coordinates from marker positions (reactive to drag)
const routeLines = computed(() => {
  const lines = []
  for (const route of props.routes) {
    const fromM = areaMarkerMap.value[route.from_area_id]
    const toM = areaMarkerMap.value[route.to_area_id]
    if (!fromM || !toM) continue
    lines.push({
      id: route.id,
      x1: displayX(fromM),
      y1: displayY(fromM),
      x2: displayX(toM),
      y2: displayY(toM),
      color: routeColors[route.route_type] || '#6b7280',
      routeType: route.route_type,
      directionRule: route.direction_rule,
    })
  }
  return lines
})

// Route legend
const routeLegendItems = computed(() => {
  const types = new Set(props.routes.map(r => r.route_type))
  return [...types].map(t => ({ type: t, color: routeColors[t] || '#6b7280', label: routeTypeLabels[t] || t }))
})

// Marker legend — only show types present on the canvas
const markerLegendItems = computed(() => {
  const types = new Set(props.markers.map(m => m.marker_type))
  return [...types]
    .filter(t => markerConfig[t])
    .map(t => ({ type: t, ...markerConfig[t] }))
})
</script>

<template>
  <div class="floorplan-canvas">
    <!-- Canvas area -->
    <div ref="canvasRef" class="canvas-area" :style="{ aspectRatio: canvasAspect }" @click="onCanvasClick">
      <!-- Floorplan image background -->
      <img
        v-if="imageUrl"
        ref="imageRef"
        :src="imageUrl"
        class="floorplan-image"
        alt="Floorplan"
        draggable="false"
        @load="onImageLoad"
      />
      <!-- Grid pattern background (fallback when no image) -->
      <svg v-else class="grid-bg" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="var(--p-surface-300)" stroke-width="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <!-- Route arrows (SVG overlay) -->
      <svg v-if="routeLines.length" class="route-overlay" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <marker
            v-for="line in routeLines"
            :key="'ah-' + line.id"
            :id="'arrowhead-' + line.id"
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" :fill="line.color" />
          </marker>
        </defs>
        <line
          v-for="line in routeLines"
          :key="'rl-' + line.id"
          :x1="line.x1"
          :y1="line.y1"
          :x2="line.x2"
          :y2="line.y2"
          :stroke="line.color"
          stroke-width="0.4"
          stroke-dasharray="1,0.5"
          :marker-end="line.directionRule !== 'bidirectional' ? `url(#arrowhead-${line.id})` : undefined"
          opacity="0.8"
        />
      </svg>

      <!-- Markers -->
      <div
        v-for="m in markers"
        :key="'m-' + m.id"
        class="marker-pin"
        :class="{ 'marker-dragging': draggingMarker?.id === m.id, 'marker-draggable': !readonly }"
        :style="{
          left: displayX(m) + '%',
          top: displayY(m) + '%',
          '--marker-color': getMarkerColor(m.marker_type),
        }"
        @click.stop="onMarkerClicked($event, m)"
        @pointerdown="onMarkerPointerDown($event, m)"
        @mouseenter="hoveredMarker = m.id"
        @mouseleave="hoveredMarker = null"
      >
        <i :class="'mdi ' + getMarkerIcon(m.marker_type)" />
        <!-- Tooltip -->
        <div class="marker-tooltip" v-if="hoveredMarker === m.id && !draggingMarker">
          <div class="tooltip-title">{{ m.label }}</div>
          <div class="tooltip-sub">{{ markerConfig[m.marker_type]?.label || m.marker_type }}</div>
          <div v-if="!readonly" class="tooltip-hint">Kéo để di chuyển</div>
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
    <div class="canvas-legend" v-if="scars.length > 0 || markers.length > 0 || routeLines.length > 0">
      <div class="legend-section" v-if="scars.length > 0">
        <span class="legend-title">Loại scar:</span>
        <span v-for="item in legendItems" :key="item.type" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
      </div>
      <div class="legend-section" v-if="markers.length > 0">
        <span class="legend-title">Khu vực:</span>
        <span v-for="item in markerLegendItems" :key="item.type" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }">
            <i :class="'mdi ' + item.icon" style="font-size: 0.5rem; color: #fff;" />
          </span>
          {{ item.label }}
        </span>
      </div>
      <div class="legend-section" v-if="routeLegendItems.length > 0">
        <span class="legend-title">Luồng:</span>
        <span v-for="item in routeLegendItems" :key="item.type" class="legend-item">
          <span class="legend-line" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
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
  /* aspect-ratio set dynamically via :style to match loaded image */
  background: var(--p-surface-100);
  border: 1px solid var(--p-surface-300);
  border-radius: var(--p-border-radius);
  overflow: hidden;
  cursor: default;
}
.floorplan-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  user-select: none;
}
.grid-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* ── Route arrows overlay ────────────────────────────────────── */
.route-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

/* ── Marker pins ─────────────────────────────────────── */
.marker-pin {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--marker-color, var(--p-primary-color));
  color: #fff;
  border-radius: 50%;
  font-size: 0.8rem;
  cursor: pointer;
  z-index: 2;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  border: 2px solid rgba(255,255,255,0.8);
}
.marker-pin:hover {
  transform: translate(-50%, -50%) scale(1.2);
  z-index: 10;
}
.marker-draggable {
  cursor: grab;
  touch-action: none;
}
.marker-dragging {
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(1.3);
  z-index: 50;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  opacity: 0.9;
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
.tooltip-hint {
  opacity: 0.6;
  font-size: 0.65rem;
  font-style: italic;
  margin-top: 2px;
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
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.legend-line {
  width: 16px;
  height: 3px;
  border-radius: 2px;
  display: inline-block;
}
</style>
