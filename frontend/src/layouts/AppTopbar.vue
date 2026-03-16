<script setup>
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth.js'

const emit = defineEmits(['toggle-sidebar'])
const authStore = useAuthStore()
</script>

<template>
  <header class="app-topbar">
    <div class="topbar-left">
      <Button
        icon="pi pi-bars"
        text
        rounded
        severity="secondary"
        @click="emit('toggle-sidebar')"
        aria-label="Toggle sidebar"
      />
    </div>

    <div class="topbar-right">
      <Button
        icon="pi pi-bell"
        text
        rounded
        severity="secondary"
        aria-label="Thông báo"
        v-tooltip.bottom="'Thông báo (Sprint 10)'"
        disabled
      />
      <span class="user-greeting">
        <i class="pi pi-user"></i>
        {{ authStore.fullName }}
      </span>
      <Button
        icon="pi pi-sign-out"
        text
        rounded
        severity="secondary"
        @click="authStore.logout()"
        aria-label="Đăng xuất"
        v-tooltip.bottom="'Đăng xuất'"
      />
    </div>
  </header>
</template>

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
