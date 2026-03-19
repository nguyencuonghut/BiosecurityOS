<script setup>
import { useLayout } from '@/layouts/composables/layout'
import { useOfflineQueue } from '@/composables/useOfflineQueue'
import AppFooter from '@/layouts/AppFooter.vue'
import AppSidebar from '@/layouts/AppSidebar.vue'
import AppTopbar from '@/layouts/AppTopbar.vue'
import Toast from 'primevue/toast'
import Tag from 'primevue/tag'

const { layoutState, containerClass, hideMobileMenu } = useLayout()
const { isOnline } = useOfflineQueue()
</script>

<template>
  <div class="layout-wrapper" :class="containerClass">
    <AppTopbar />
    <AppSidebar />
    <div class="layout-main-container">
      <Tag
        v-if="!isOnline"
        value="Ngoại tuyến — Dữ liệu sẽ được đồng bộ khi có mạng"
        severity="warn"
        icon="pi pi-wifi"
        class="offline-banner"
      />
      <div class="layout-main">
        <router-view />
      </div>
      <AppFooter />
    </div>
    <div class="layout-mask animate-fadein" @click="hideMobileMenu" />
    <Toast />
  </div>
</template>

<style scoped>
.layout-wrapper {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: var(--p-surface-ground);
}

.layout-main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  margin-left: 280px;
  padding-top: 70px;
  position: relative;
  z-index: 1;
  transition: margin-left 0.3s ease;
}

.layout-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--p-surface-ground);
}

.layout-mask {
  position: fixed;
  height: 100%;
  width: 100%;
  top: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 998;
  display: none;
}

.layout-static-inactive .layout-main-container {
  margin-left: 60px;
}

.layout-static-inactive :deep(.layout-sidebar) {
  width: 60px;
}

.layout-static-inactive :deep(.sidebar-nav) {
  padding: 0.75rem 0.5rem;
  align-items: center;
}

.layout-static-inactive :deep(.nav-item) {
  justify-content: center;
  padding: 0.75rem;
  width: 40px;
  height: 40px;
  gap: 0;
}

.layout-static-inactive :deep(.sidebar-brand) {
  justify-content: center;
  padding: 1.5rem 0.5rem;
}

.layout-static-inactive :deep(.brand-text),
.layout-static-inactive :deep(.nav-label) {
  opacity: 0;
  width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.layout-mobile-active .layout-mask {
  display: block;
}

.offline-banner {
  width: 100%;
  border-radius: 0;
  justify-content: center;
  font-size: 0.85rem;
}

/* Mobile responsive */
@media screen and (max-width: 991px) {
  .layout-main-container {
    margin-left: 0;
  }
}

/* Animations */
@keyframes fadein {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-fadein {
  animation: fadein 0.15s linear;
}
</style>
