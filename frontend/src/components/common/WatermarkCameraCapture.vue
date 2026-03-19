<script setup>
/**
 * WatermarkCameraCapture.vue — Sprint 11 (FR-20)
 *
 * Mobile evidence capture with GPS + timestamp + user info watermark.
 * Emits:  capture(blob, metadata)
 */
import { ref, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth.js'
import Button from 'primevue/button'

const emit = defineEmits(['capture'])
const authStore = useAuthStore()

const videoRef = ref(null)
const canvasRef = ref(null)
const previewSrc = ref(null)
const streaming = ref(false)
const capturing = ref(false)
const error = ref(null)
let mediaStream = null

async function startCamera() {
  error.value = null
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 960 } },
      audio: false,
    })
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      await videoRef.value.play()
      streaming.value = true
    }
  } catch (err) {
    error.value = 'Không thể truy cập camera. Vui lòng cấp quyền camera.'
    console.error('Camera error:', err)
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop())
    mediaStream = null
  }
  streaming.value = false
}

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          lat: pos.coords.latitude.toFixed(6),
          lng: pos.coords.longitude.toFixed(6),
          accuracy: Math.round(pos.coords.accuracy),
        }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 10000 }
    )
  })
}

async function capturePhoto() {
  if (!videoRef.value || !canvasRef.value) return
  capturing.value = true

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  // Draw video frame
  ctx.drawImage(video, 0, 0)

  // Get metadata
  const now = new Date()
  const timestamp = now.toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
  const user = authStore.fullName || authStore.username || 'Unknown'
  const geo = await getLocation()

  // Draw watermark overlay
  const lines = [`${timestamp}`, `User: ${user}`]
  if (geo) {
    lines.push(`GPS: ${geo.lat}, ${geo.lng} (±${geo.accuracy}m)`)
  }

  const fontSize = Math.max(14, Math.floor(canvas.width / 50))
  ctx.font = `bold ${fontSize}px sans-serif`
  ctx.textBaseline = 'bottom'

  const padding = fontSize * 0.5
  const lineHeight = fontSize * 1.4
  const blockHeight = lines.length * lineHeight + padding * 2

  // Semi-transparent background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.55)'
  ctx.fillRect(0, canvas.height - blockHeight, canvas.width, blockHeight)

  // Text
  ctx.fillStyle = '#ffffff'
  lines.forEach((line, i) => {
    const y = canvas.height - blockHeight + padding + (i + 1) * lineHeight
    ctx.fillText(line, padding, y)
  })

  // Convert to blob
  canvas.toBlob(
    (blob) => {
      previewSrc.value = URL.createObjectURL(blob)
      const metadata = {
        timestamp: now.toISOString(),
        user,
        gps: geo,
      }
      emit('capture', blob, metadata)
      capturing.value = false
    },
    'image/jpeg',
    0.9
  )
}

function retake() {
  if (previewSrc.value) {
    URL.revokeObjectURL(previewSrc.value)
    previewSrc.value = null
  }
}

onBeforeUnmount(() => {
  stopCamera()
  if (previewSrc.value) URL.revokeObjectURL(previewSrc.value)
})
</script>

<template>
  <div class="wcc-container">
    <!-- Error -->
    <div v-if="error" class="wcc-error">
      <i class="pi pi-exclamation-triangle"></i>
      {{ error }}
    </div>

    <!-- Preview after capture -->
    <div v-if="previewSrc" class="wcc-preview">
      <img :src="previewSrc" alt="Captured photo" class="wcc-preview-img" />
      <div class="wcc-preview-actions">
        <Button label="Chụp lại" icon="pi pi-refresh" severity="secondary" @click="retake" />
      </div>
    </div>

    <!-- Camera view -->
    <div v-else class="wcc-camera">
      <video
        v-show="streaming"
        ref="videoRef"
        autoplay
        playsinline
        muted
        class="wcc-video"
      />
      <canvas ref="canvasRef" class="wcc-canvas" />

      <div class="wcc-controls">
        <Button
          v-if="!streaming"
          label="Mở Camera"
          icon="pi pi-camera"
          @click="startCamera"
        />
        <template v-else>
          <Button
            label="Chụp ảnh"
            icon="pi pi-camera"
            :loading="capturing"
            @click="capturePhoto"
          />
          <Button
            label="Tắt Camera"
            icon="pi pi-times"
            severity="secondary"
            @click="stopCamera"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wcc-container {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
}

.wcc-error {
  padding: 1rem;
  background: var(--p-red-50);
  color: var(--p-red-700);
  border-radius: 8px;
  text-align: center;
  margin-bottom: 1rem;
}

.wcc-video {
  width: 100%;
  border-radius: 8px;
  background: #000;
}

.wcc-canvas {
  display: none;
}

.wcc-controls {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 0.75rem;
  flex-wrap: wrap;
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
  .wcc-controls .p-button {
    min-height: 3rem;
    font-size: 1rem;
  }
}
</style>
