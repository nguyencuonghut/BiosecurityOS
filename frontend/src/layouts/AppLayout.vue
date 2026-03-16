<script setup>
import AppTopbar from '@/layouts/AppTopbar.vue'
import AppSidebar from '@/layouts/AppSidebar.vue'
import { ref } from 'vue'

const sidebarVisible = ref(true)

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}
</script>

<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': !sidebarVisible }">
    <AppSidebar :visible="sidebarVisible" />
    <div class="app-main">
      <AppTopbar @toggle-sidebar="toggleSidebar" />
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-content {
  flex: 1;
  padding: 1.5rem;
  background: var(--p-surface-ground);
  overflow-y: auto;
}
</style>
