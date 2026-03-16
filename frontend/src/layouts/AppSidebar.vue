<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

defineProps({
  visible: { type: Boolean, default: true },
})

const route = useRoute()
const authStore = useAuthStore()

const menuItems = computed(() => {
  const all = [
    { label: 'Dashboard', icon: 'pi pi-chart-bar', to: '/', permission: null },
    { label: 'Trại', icon: 'pi pi-building', to: '/farms', permission: 'FARM_READ' },
    { label: 'Scorecard', icon: 'pi pi-list', to: '/scorecards', permission: 'SCORECARD_READ' },
    { label: 'Đánh giá', icon: 'pi pi-clipboard', to: '/assessments', permission: 'ASSESSMENT_READ' },
    { label: 'Killer Metrics', icon: 'pi pi-bolt', to: '/killer-metrics/events', permission: 'KILLER_EVENT_READ' },
    { label: 'Cases', icon: 'pi pi-exclamation-triangle', to: '/cases', permission: 'CASE_CREATE' },
    { label: 'Tasks', icon: 'pi pi-check-square', to: '/tasks', permission: 'TASK_CREATE' },
    { label: 'Scar Map', icon: 'pi pi-map', to: '/scars', permission: 'SCAR_READ' },
    { label: 'Bài học', icon: 'pi pi-book', to: '/lessons', permission: 'SCAR_READ' },
    { label: 'Admin', icon: 'pi pi-cog', to: '/admin/users', permission: 'USER_ADMIN' },
    { label: 'KM Definitions', icon: 'pi pi-exclamation-circle', to: '/killer-metrics/definitions', permission: 'KILLER_EVENT_WRITE' },
  ]
  return all.filter((item) => !item.permission || authStore.hasPermission(item.permission))
})

function isActive(to) {
  if (to === '/') return route.path === '/'
  return route.path === to || route.path.startsWith(to + '/')
}
</script>

<template>
  <aside v-if="visible" class="app-sidebar">
    <div class="sidebar-brand">
      <i class="pi pi-shield"></i>
      <span class="brand-text">BIOSEC OS</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.to) }"
      >
        <i :class="item.icon"></i>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 240px;
  min-height: 100vh;
  background: var(--p-surface-card);
  border-right: 1px solid var(--p-surface-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--p-primary-color);
  border-bottom: 1px solid var(--p-surface-border);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: var(--p-text-color);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--p-surface-hover);
}

.nav-item.active {
  background: var(--p-primary-color);
  color: var(--p-primary-contrast-color);
}

.nav-item i {
  font-size: 1.1rem;
  width: 1.25rem;
  text-align: center;
}
</style>
