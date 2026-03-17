<script setup>
import { useLayout } from '@/layouts/composables/layout'
import AppFooter from '@/layouts/AppFooter.vue'
import AppSidebar from '@/layouts/AppSidebar.vue'
import AppTopbar from '@/layouts/AppTopbar.vue'
import Toast from 'primevue/toast'

const { layoutState, containerClass, hideMobileMenu } = useLayout()
</script>

<template>
  <div class="layout-wrapper" :class="containerClass">
    <AppTopbar />
    <AppSidebar />
    <div class="layout-main-container">
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
  background-color: var(--p-surface-overlay);
  z-index: 998;
  display: none;
}

.layout-static-inactive .layout-main-container {
  margin-left: 60px;
}

.layout-mobile-active .layout-mask {
  display: block;
}

/* Mobile responsive */
@media screen and (max-width: 991px) {
  .layout-main-container {
    margin-left: 0;
  }

  .layout-mobile-active .layout-main-container {
    margin-left: 280px;
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
