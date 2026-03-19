<script setup>
/**
 * WatermarkCameraCapture.vue — Sprint 11 (FR-20)
 *
 * Evidence capture via native camera (input capture="environment").
 * - No getUserMedia permission popup — opens phone camera directly.
 * - Reads EXIF DateTimeOriginal to reject old photos (max 2 min).
 * - Draws watermark (timestamp + user + GPS) onto photo via Canvas.
 * Emits:  capture(blob, metadata)
 */
import { ref, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import Button from 'primevue/button'

const props = defineProps({
  maxAgeSeconds: { type: Number, default: 120 },
})
const emit = defineEmits(['capture'])
const authStore = useAuthStore()

const fileInputRef = ref(null)
const canvasRef = ref(null)
const previewSrc = ref(null)
const processing = ref(false)
const error = ref(null)

/* ── EXIF helpers (lightweight, no external lib) ── */

function readExifDate(arrayBuffer) {
  const view = new DataView(arrayBuffer)
  // Check JPEG SOI
  if (view.getUint16(0) !== 0xFFD8) return null

  let offset = 2
  while (offset < view.byteLength - 1) {
    const marker = view.getUint16(offset)
    if (marker === 0xFFE1) {
      // APP1 — EXIF
      const length = view.getUint16(offset + 2)
      return parseExifBlock(view, offset + 4, length - 2)
    }
    if ((marker & 0xFF00) !== 0xFF00) break
    offset += 2 + view.getUint16(offset + 2)
  }
  return null
}

function parseExifBlock(view, start, length) {
  // "Exif\0\0"
  const exifHeader = String.fromCharCode(
    view.getUint8(start), view.getUint8(start + 1),
    view.getUint8(start + 2), view.getUint8(start + 3),
  )
  if (exifHeader !== 'Exif') return null

  const tiffStart = start + 6
  const littleEndian = view.getUint16(tiffStart) === 0x4949

  const ifdOffset = view.getUint32(tiffStart + 4, littleEndian)
  return findDateInIFD(view, tiffStart, tiffStart + ifdOffset, littleEndian, length)
}

function findDateInIFD(view, tiffStart, ifdStart, le, maxLen) {
  const count = view.getUint16(ifdStart, le)
  for (let i = 0; i < count; i++) {
    const entryOff = ifdStart + 2 + i * 12
    if (entryOff + 12 > view.byteLength) break
    const tag = view.getUint16(entryOff, le)
    // 0x9003 = DateTimeOriginal, 0x9004 = DateTimeDigitized, 0x0132 = DateTime
    if (tag === 0x9003 || tag === 0x9004 || tag === 0x0132) {
      const valOffset = view.getUint32(entryOff + 8, le)
      const strStart = tiffStart + valOffset
      if (strStart + 19 > view.byteLength) continue
      let str = ''
      for (let j = 0; j < 19; j++) str += String.fromCharCode(view.getUint8(strStart + j))
      // "YYYY:MM:DD HH:MM:SS" → ISO
      const iso = str.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3').replace(' ', 'T')
      const d = new Date(iso)
      if (!isNaN(d.getTime())) return d
    }
  }
  // Check sub-IFD (ExifIFDPointer = 0x8769)
  for (let i = 0; i < count; i++) {
    const entryOff = ifdStart + 2 + i * 12
    if (entryOff + 12 > view.byteLength) break
    if (view.getUint16(entryOff, le) === 0x8769) {
      const subIfdOff = view.getUint32(entryOff + 8, le)
      return findDateInIFD(view, tiffStart, tiffStart + subIfdOff, le, maxLen)
    }
  }
  return null
}

/* ── GPS ── */

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) { resolve(null); return }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({
        lat: pos.coords.latitude.toFixed(6),
        lng: pos.coords.longitude.toFixed(6),
        accuracy: Math.round(pos.coords.accuracy),
      }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  })
}

/* ── Watermark drawing ── */

function drawWatermark(ctx, canvas, lines) {
  const fontSize = Math.max(14, Math.floor(canvas.width / 50))
  ctx.font = `bold ${fontSize}px sans-serif`
  ctx.textBaseline = 'bottom'

  const padding = fontSize * 0.5
  const lineHeight = fontSize * 1.4
  const blockHeight = lines.length * lineHeight + padding * 2

  ctx.fillStyle = 'rgba(0, 0, 0, 0.55)'
  ctx.fillRect(0, canvas.height - blockHeight, canvas.width, blockHeight)

  ctx.fillStyle = '#ffffff'
  lines.forEach((line, i) => {
    const y = canvas.height - blockHeight + padding + (i + 1) * lineHeight
    ctx.fillText(line, padding, y)
  })
}

/* ── Main flow ── */

function openCamera() {
  error.value = null
  fileInputRef.value?.click()
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // Reset input so same file can be re-selected
  e.target.value = ''

  error.value = null
  processing.value = true

  try {
    // 1. Validate EXIF timestamp — reject old photos
    const buffer = await file.arrayBuffer()
    const exifDate = readExifDate(buffer)
    if (exifDate) {
      const ageSeconds = (Date.now() - exifDate.getTime()) / 1000
      if (ageSeconds > props.maxAgeSeconds) {
        error.value = `Ảnh đã chụp ${Math.round(ageSeconds / 60)} phút trước. Vui lòng chụp ảnh mới.`
        processing.value = false
        return
      }
    }

    // 2. Load image onto canvas
    const img = new Image()
    const objectUrl = URL.createObjectURL(file)
    await new Promise((resolve, reject) => {
      img.onload = resolve
      img.onerror = reject
      img.src = objectUrl
    })
    URL.revokeObjectURL(objectUrl)

    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')
    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight
    ctx.drawImage(img, 0, 0)

    // 3. Gather metadata
    const now = new Date()
    const timestamp = now.toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
    const user = authStore.fullName || authStore.username || 'Unknown'
    const geo = await getLocation()

    // 4. Draw watermark
    const lines = [timestamp, `User: ${user}`]
    if (geo) lines.push(`GPS: ${geo.lat}, ${geo.lng} (±${geo.accuracy}m)`)
    drawWatermark(ctx, canvas, lines)

    // 5. Export watermarked image
    canvas.toBlob(
      (blob) => {
        previewSrc.value = URL.createObjectURL(blob)
        emit('capture', blob, { timestamp: now.toISOString(), user, gps: geo })
        processing.value = false
      },
      'image/jpeg',
      0.9,
    )
  } catch {
    error.value = 'Không thể xử lý ảnh. Vui lòng thử lại.'
    processing.value = false
  }
}

function retake() {
  if (previewSrc.value) {
    URL.revokeObjectURL(previewSrc.value)
    previewSrc.value = null
  }
  error.value = null
}

onBeforeUnmount(() => {
  if (previewSrc.value) URL.revokeObjectURL(previewSrc.value)
})
</script>

<template>
  <div class="wcc-container">
    <!-- Hidden file input — opens native camera -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      class="wcc-file-input"
      @change="onFileSelected"
    />

    <!-- Error -->
    <div v-if="error" class="wcc-error">
      <i class="pi pi-exclamation-triangle"></i>
      {{ error }}
      <div style="margin-top: 0.5rem;">
        <Button label="Thử lại" icon="pi pi-refresh" severity="secondary" size="small" @click="openCamera" />
      </div>
    </div>

    <!-- Preview after capture -->
    <div v-if="previewSrc" class="wcc-preview">
      <img :src="previewSrc" alt="Captured photo" class="wcc-preview-img" />
      <div class="wcc-preview-actions">
        <Button label="Chụp lại" icon="pi pi-refresh" severity="secondary" @click="retake" />
      </div>
    </div>

    <!-- Capture button -->
    <div v-else-if="!error" class="wcc-capture">
      <Button
        label="Chụp ảnh"
        icon="pi pi-camera"
        :loading="processing"
        @click="openCamera"
      />
      <p class="wcc-hint">Mở camera để chụp ảnh bằng chứng</p>
    </div>

    <canvas ref="canvasRef" class="wcc-canvas" />
  </div>
</template>

<style scoped>
.wcc-container {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
}

.wcc-file-input {
  display: none;
}

.wcc-error {
  padding: 1rem;
  background: var(--p-red-50);
  color: var(--p-red-700);
  border-radius: 8px;
  text-align: center;
  margin-bottom: 1rem;
}

.wcc-canvas {
  display: none;
}

.wcc-capture {
  text-align: center;
  padding: 2rem 1rem;
}

.wcc-hint {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}

.wcc-preview-img {
  width: 100%;
  border-radius: 8px;
}

.wcc-preview-actions {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

@media screen and (max-width: 768px) {
  .wcc-capture .p-button {
    min-height: 3rem;
    font-size: 1rem;
  }
}
</style>
