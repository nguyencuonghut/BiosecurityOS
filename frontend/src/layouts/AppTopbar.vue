<script setup>
import { useLayout } from '@/layouts/composables/layout'
import { useAuthStore } from '@/stores/auth.js'
import Button from 'primevue/button'

const { toggleSidebar } = useLayout()
const authStore = useAuthStore()
</script>

<template>
  <header class="layout-topbar">
    <div class="topbar-left">
      <Button
        icon="pi pi-bars"
        text
        rounded
        class="layout-menu-button"
        @click="toggleSidebar"
        aria-label="Toggle sidebar"
      />
      <span class="app-title">Biosecurity OS</span>
    </div>

    <div class="topbar-right">
      <Button
        icon="pi pi-bell"
        text
        rounded
        severity="secondary"
        aria-label="Notifications"
      />
      <span class="user-greeting">
        <i class="pi pi-user"></i>
        {{ authStore.fullName || authStore.username }}
      </span>
      <Button
        icon="pi pi-sign-out"
        text
        rounded
        severity="secondary"
        aria-label="Logout"
        @click="authStore.logout()"
      />
    </div>
  </header>
</template>

<style scoped>
.layout-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: var(--p-surface-card);
  border-bottom: 1px solid var(--p-surface-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 1000;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--p-primary-color);
  display: none;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-color);
  white-space: nowrap;
}

.user-greeting i {
  font-size: 1rem;
}

@media screen and (max-width: 991px) {
  .app-title {
    display: inline;
  }

  .user-greeting {
    display: none;
  }
}
</style>

<style scoped>
.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.5rem;
  background: var(--p-surface-card);
  border-bottom: 1px solid var(--p-surface-border);
  min-height: 3.5rem;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--p-text-color);
}
</style>
