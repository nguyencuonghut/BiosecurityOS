/**
 * useOfflineQueue — composable for Service Worker offline queue (Sprint 11, NFR-10).
 *
 * Registers SW, listens for online/offline, triggers queue replay.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'

const isOnline = ref(navigator.onLine)
const pendingSynced = ref(false)

let swRegistration = null

export function useOfflineQueue() {
  function onOnline() {
    isOnline.value = true
    // Tell SW to replay queued requests
    if (swRegistration?.active) {
      swRegistration.active.postMessage({ type: 'REPLAY_QUEUE' })
    }
  }

  function onOffline() {
    isOnline.value = false
    pendingSynced.value = false
  }

  function onSWMessage(event) {
    if (event.data?.type === 'QUEUE_REPLAYED') {
      pendingSynced.value = true
    }
  }

  onMounted(async () => {
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)

    if ('serviceWorker' in navigator && import.meta.env.PROD) {
      try {
        swRegistration = await navigator.serviceWorker.register('/sw.js')
        navigator.serviceWorker.addEventListener('message', onSWMessage)
      } catch (err) {
        console.warn('SW registration failed:', err)
      }
    }
  })

  onBeforeUnmount(() => {
    window.removeEventListener('online', onOnline)
    window.removeEventListener('offline', onOffline)
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.removeEventListener('message', onSWMessage)
    }
  })

  return { isOnline, pendingSynced }
}
