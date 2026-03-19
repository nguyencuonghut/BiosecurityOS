<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useLayout } from '@/layouts/composables/layout'
import { useAuthStore } from '@/stores/auth.js'
import { useNotificationStore } from '@/stores/notification.js'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Popover from 'primevue/popover'

const router = useRouter()
const { toggleSidebar } = useLayout()
const authStore = useAuthStore()
const notifStore = useNotificationStore()
const notifPopover = ref()
let pollTimer = null

onMounted(() => {
  if (authStore.isAuthenticated) {
    notifStore.fetchUnreadCount()
    pollTimer = setInterval(() => notifStore.fetchUnreadCount(), 60000)
  }
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function toggleNotifPopover(event) {
  notifPopover.value.toggle(event)
  if (!notifStore.notifications.length) {
    notifStore.filters.page = 1
    notifStore.filters.page_size = 5
    notifStore.fetchNotifications()
  }
}

async function onNotifClick(notif) {
  if (!notif.read_at) await notifStore.markAsRead(notif.id)
  notifPopover.value.hide()
  if (notif.entity_type && notif.entity_id) {
    const routeMap = { case: 'CaseDetail', task: 'TaskDetail', farm: 'FarmDetail' }
    const name = routeMap[notif.entity_type]
    if (name) router.push({ name, params: { id: notif.entity_id } })
  }
}

function goToNotifications() {
  notifPopover.value.hide()
  router.push('/notifications')
}

function timeAgo(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Vừa xong'
  if (mins < 60) return `${mins} phút trước`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} giờ trước`
  return `${Math.floor(hrs / 24)} ngày trước`
}
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
      <div class="notif-bell-wrapper">
        <Button
          icon="pi pi-bell"
          text
          rounded
          severity="secondary"
          aria-label="Notifications"
          @click="toggleNotifPopover"
        />
        <Badge
          v-if="notifStore.unreadCount > 0"
          :value="notifStore.unreadCount > 99 ? '99+' : notifStore.unreadCount"
          severity="danger"
          class="notif-badge"
        />
      </div>

      <Popover ref="notifPopover" class="notif-popover">
        <div class="notif-dropdown">
          <div class="notif-dropdown-header">
            <span class="notif-dropdown-title">Thông báo</span>
            <Button label="Xem tất cả" text size="small" @click="goToNotifications" />
          </div>
          <div v-if="notifStore.loading" class="notif-loading">
            <i class="pi pi-spin pi-spinner"></i> Đang tải...
          </div>
          <div v-else-if="!notifStore.notifications.length" class="notif-empty">
            Không có thông báo nào.
          </div>
          <ul v-else class="notif-list">
            <li
              v-for="n in notifStore.notifications"
              :key="n.id"
              class="notif-item"
              :class="{ unread: !n.read_at }"
              @click="onNotifClick(n)"
            >
              <div class="notif-item-title">{{ n.title }}</div>
              <div class="notif-item-body">{{ n.body }}</div>
              <div class="notif-item-time">{{ timeAgo(n.sent_at || n.created_at) }}</div>
            </li>
          </ul>
        </div>
      </Popover>

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

.notif-bell-wrapper {
  position: relative;
  display: inline-flex;
}

.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  pointer-events: none;
  font-size: 0.65rem;
  min-width: 1.2rem;
  height: 1.2rem;
  line-height: 1.2rem;
}

.notif-dropdown {
  width: 22rem;
  max-height: 24rem;
  overflow-y: auto;
}

.notif-dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--p-surface-border);
}

.notif-dropdown-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.notif-loading,
.notif-empty {
  padding: 2rem;
  text-align: center;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.notif-item {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--p-surface-border);
  cursor: pointer;
  transition: background 0.15s;
}

.notif-item:hover {
  background: var(--p-surface-hover);
}

.notif-item.unread {
  background: var(--p-primary-50, rgba(var(--p-primary-500), 0.06));
}

.notif-item-title {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.15rem;
}

.notif-item-body {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notif-item-time {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  margin-top: 0.2rem;
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
