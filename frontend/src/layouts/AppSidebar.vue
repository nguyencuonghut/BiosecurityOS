<script setup>
import { useLayout } from '@/layouts/composables/layout'
import { useAuthStore } from '@/stores/auth.js'
import { useRoute } from 'vue-router'
import { ref, watch, onBeforeUnmount, computed } from 'vue'

const { layoutState } = useLayout()
const authStore = useAuthStore()
const route = useRoute()
const sidebarRef = ref(null)
let outsideClickListener = null

// Groups that are expanded (by group label)
const expandedGroups = ref(new Set(['Cấu hình']))

function toggleGroup(label) {
  if (expandedGroups.value.has(label)) {
    expandedGroups.value.delete(label)
  } else {
    expandedGroups.value.add(label)
  }
  // trigger reactivity
  expandedGroups.value = new Set(expandedGroups.value)
}

const navTree = computed(() => {
  const can = (perm) => !perm || authStore.hasPermission(perm)
  const flat = [
    { label: 'Dashboard', icon: 'pi pi-chart-bar', to: '/', permission: null },
    { label: 'Trại', icon: 'pi pi-building', to: '/farms', permission: 'FARM_READ' },
    { label: 'Scorecard', icon: 'pi pi-list', to: '/scorecards', permission: 'SCORECARD_READ' },
    { label: 'Đánh giá', icon: 'pi pi-clipboard', to: '/assessments', permission: 'ASSESSMENT_READ' },
    { label: 'Killer Metrics', icon: 'pi pi-bolt', to: '/killer-metrics/events', permission: 'KILLER_EVENT_READ' },
    { label: 'Cases', icon: 'pi pi-exclamation-triangle', to: '/cases', permission: 'CASE_CREATE' },
    { label: 'Tasks', icon: 'pi pi-check-square', to: '/tasks', permission: 'TASK_READ' },
    { label: 'Scar Map', icon: 'pi pi-map', to: '/scars', permission: 'SCAR_READ' },
    { label: 'Bài học', icon: 'pi pi-book', to: '/lessons', permission: 'LESSON_READ' },
    { label: 'Báo cáo', icon: 'pi pi-file-export', to: '/reports', permission: 'REPORT_GENERATE' },
    { label: 'Thông báo', icon: 'pi pi-bell', to: '/notifications', permission: 'NOTIFICATION_READ' },
    { label: 'Người dùng', icon: 'pi pi-users', to: '/admin/users', permission: 'USER_ADMIN' },
    { label: 'Phân quyền', icon: 'pi pi-shield', to: '/admin/roles', permission: 'USER_ADMIN' },
    { label: 'KM Definitions', icon: 'pi pi-exclamation-circle', to: '/killer-metrics/definitions', permission: 'KILLER_EVENT_WRITE' },
    { label: 'Nhật ký', icon: 'pi pi-history', to: '/admin/audit-logs', permission: 'AUDIT_LOG_READ' },
    {
      label: 'Cấu hình',
      icon: 'pi pi-sliders-h',
      permission: 'USER_ADMIN',
      children: [
        { label: 'Loại khu vực', icon: 'pi pi-tag', to: '/config/area-types', permission: 'USER_ADMIN' },
      ],
    },
  ]
  return flat
    .filter((item) => can(item.permission))
    .map((item) => ({
      ...item,
      children: item.children?.filter((c) => can(c.permission)),
    }))
    .filter((item) => !item.children || item.children.length > 0)
})

function isActive(to) {
  if (to === '/') return route.path === '/'
  return route.path === to || route.path.startsWith(to + '/')
}

function isGroupActive(item) {
  return item.children?.some((c) => isActive(c.to))
}

watch(
  () => route.path,
  () => {
    layoutState.mobileMenuActive = false
  }
)

const bindOutsideClickListener = () => {
  if (!outsideClickListener) {
    outsideClickListener = (event) => {
      if (isOutsideClicked(event)) {
        layoutState.mobileMenuActive = false
      }
    }
    document.addEventListener('click', outsideClickListener)
  }
}

const unbindOutsideClickListener = () => {
  if (outsideClickListener) {
    document.removeEventListener('click', outsideClickListener)
    outsideClickListener = null
  }
}

const isOutsideClicked = (event) => {
  const topbarButtonEl = document.querySelector('.layout-menu-button')
  return !(
    sidebarRef.value?.isSameNode(event.target) ||
    sidebarRef.value?.contains(event.target) ||
    topbarButtonEl?.isSameNode(event.target) ||
    topbarButtonEl?.contains(event.target)
  )
}

watch(
  () => layoutState.mobileMenuActive,
  (newVal) => {
    if (newVal) {
      bindOutsideClickListener()
    } else {
      unbindOutsideClickListener()
    }
  }
)

onBeforeUnmount(() => {
  unbindOutsideClickListener()
})
</script>

<template>
  <div ref="sidebarRef" class="layout-sidebar">
    <div class="sidebar-brand">
      <i class="pi pi-shield"></i>
      <span class="brand-text">BIOSEC OS</span>
    </div>

    <nav class="sidebar-nav">
      <template v-for="item in navTree" :key="item.label">
        <!-- Group with children -->
        <template v-if="item.children">
          <button
            class="nav-item nav-group"
            :class="{ 'group-active': isGroupActive(item) }"
            @click="toggleGroup(item.label)"
          >
            <i :class="item.icon"></i>
            <span class="nav-label">{{ item.label }}</span>
            <i
              class="nav-chevron pi"
              :class="expandedGroups.has(item.label) ? 'pi-chevron-down' : 'pi-chevron-right'"
            />
          </button>
          <div v-show="expandedGroups.has(item.label)" class="nav-children">
            <router-link
              v-for="child in item.children"
              :key="child.to"
              :to="child.to"
              class="nav-item nav-child"
              :class="{ active: isActive(child.to) }"
            >
              <i :class="child.icon"></i>
              <span class="nav-label">{{ child.label }}</span>
            </router-link>
          </div>
        </template>
        <!-- Flat item -->
        <router-link
          v-else
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <i :class="item.icon"></i>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </template>
    </nav>
  </div>
</template>

<style scoped>
.layout-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: var(--p-surface-card);
  border-right: 1px solid var(--p-surface-border);
  padding-top: 70px;
  overflow-y: auto;
  overflow-x: hidden;
  transition: transform 0.3s ease, width 0.3s ease;
  z-index: 999;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--p-primary-color);
  border-bottom: 1px solid var(--p-surface-border);
}

.brand-text {
  transition: opacity 0.3s ease;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 0.25rem;
  flex: 1;
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
  transition: all 0.15s ease;
  cursor: pointer;
  white-space: nowrap;
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
  flex-shrink: 0;
}

.nav-label {
  transition: opacity 0.3s ease;
  flex: 1;
}

.nav-group {
  width: 100%;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--p-text-color);
}

.nav-group:hover {
  background: var(--p-surface-hover);
}

.nav-group.group-active {
  color: var(--p-primary-color);
}

.nav-chevron {
  font-size: 0.75rem;
  width: auto;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.nav-children {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  margin-top: 0.1rem;
}

.nav-child {
  padding-left: 2.5rem;
  font-size: 0.85rem;
}

.layout-sidebar::-webkit-scrollbar {
  width: 6px;
}

.layout-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.layout-sidebar::-webkit-scrollbar-thumb {
  background: var(--p-surface-border);
  border-radius: 3px;
}

.layout-sidebar::-webkit-scrollbar-thumb:hover {
  background: var(--p-text-muted-color);
}

</style>
