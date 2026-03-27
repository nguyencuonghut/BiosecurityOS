<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import ProgressSpinner from 'primevue/progressspinner'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import { useUserStore } from '@/stores/user.js'

const toast = useToast()
const store = useUserStore()

const loadingRoles = ref(false)
const loadingPerms = ref(false)
const togglingId = ref(null)
const searchQuery = ref('')

// ── Module metadata ───────────────────────────────────────────
const MODULE_LABELS = {
  farm: 'Trại & Vùng',
  assessment: 'Đánh giá',
  scorecard: 'Scorecard',
  killer_metric: 'Killer Metric',
  trust_score: 'Trust Score',
  case: 'Case',
  rca: 'RCA',
  task: 'Task',
  attachment: 'Tệp đính kèm',
  scar: 'Scar Memory',
  lesson: 'Bài học',
  dashboard: 'Dashboard',
  report: 'Báo cáo',
  notification: 'Thông báo',
  audit_log: 'Nhật ký',
  iam: 'Quản trị người dùng',
}

const MODULE_ICONS = {
  farm: 'pi-home',
  assessment: 'pi-clipboard',
  scorecard: 'pi-chart-bar',
  killer_metric: 'pi-exclamation-circle',
  trust_score: 'pi-star',
  case: 'pi-folder-open',
  rca: 'pi-search',
  task: 'pi-check-square',
  attachment: 'pi-paperclip',
  scar: 'pi-bookmark',
  lesson: 'pi-book',
  dashboard: 'pi-th-large',
  report: 'pi-file-pdf',
  notification: 'pi-bell',
  audit_log: 'pi-history',
  iam: 'pi-users',
}

const SCOPE_COLORS = { global: 'info', region: 'warn', farm: 'success' }
const SCOPE_LABELS = { global: 'Toàn cục', region: 'Vùng', farm: 'Trại' }

const ACTION_COLORS = {
  VIEW:    'info',
  CREATE:  'success',
  UPDATE:  'warn',
  DELETE:  'danger',
  MANAGE:  'contrast',
  APPROVE: 'secondary',
  EXPORT:  'secondary',
}

// ── Derived ───────────────────────────────────────────────────
const permsByModule = computed(() => {
  const map = {}
  for (const p of store.permissions) {
    if (!map[p.module]) map[p.module] = []
    map[p.module].push(p)
  }
  return map
})

const allModules = computed(() => Object.keys(permsByModule.value).sort())

const filteredModules = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return allModules.value
  return allModules.value.filter((mod) => {
    const label = (MODULE_LABELS[mod] ?? mod).toLowerCase()
    if (label.includes(q)) return true
    return permsByModule.value[mod]?.some(
      (p) => p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q)
    )
  })
})

const filteredPermsByModule = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return permsByModule.value
  const result = {}
  for (const mod of filteredModules.value) {
    const label = (MODULE_LABELS[mod] ?? mod).toLowerCase()
    if (label.includes(q)) {
      result[mod] = permsByModule.value[mod]
    } else {
      result[mod] = permsByModule.value[mod]?.filter(
        (p) => p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q)
      )
    }
  }
  return result
})

const selectedPermissionIds = computed(
  () => new Set(store.selectedRole?.permission_ids ?? [])
)

const grantedCount = computed(() => selectedPermissionIds.value.size)
const totalCount = computed(() => store.permissions.length)
const grantedPct = computed(() =>
  totalCount.value ? Math.round((grantedCount.value / totalCount.value) * 100) : 0
)

function isGranted(permId) {
  return selectedPermissionIds.value.has(permId)
}

function moduleGrantedCount(mod) {
  return (filteredPermsByModule.value[mod] ?? []).filter((p) => isGranted(p.id)).length
}

function isModuleAllGranted(mod) {
  return permsByModule.value[mod]?.every((p) => isGranted(p.id)) ?? false
}

function isModulePartiallyGranted(mod) {
  const perms = permsByModule.value[mod] ?? []
  const granted = perms.filter((p) => isGranted(p.id)).length
  return granted > 0 && granted < perms.length
}

// ── Module toggle ─────────────────────────────────────────────
async function toggleModule(mod) {
  if (!store.selectedRole) return
  const perms = permsByModule.value[mod] ?? []
  const allGranted = isModuleAllGranted(mod)
  for (const p of perms) {
    if (allGranted) {
      if (isGranted(p.id)) await doRevoke(p.id, false)
    } else {
      if (!isGranted(p.id)) await doGrant(p.id, false)
    }
  }
  toast.add({ severity: 'success', summary: 'Đã cập nhật module', detail: MODULE_LABELS[mod] ?? mod, life: 2000 })
}

// ── Permission toggle ─────────────────────────────────────────
async function doGrant(permId, showToast = true) {
  togglingId.value = permId
  try {
    await store.grantPermission(store.selectedRole.id, permId)
    if (showToast) toast.add({ severity: 'success', summary: 'Đã cấp quyền', life: 1200 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e?.response?.data?.error?.message ?? e.message, life: 3000 })
  } finally {
    togglingId.value = null
  }
}

async function doRevoke(permId, showToast = true) {
  togglingId.value = permId
  try {
    await store.revokePermission(store.selectedRole.id, permId)
    if (showToast) toast.add({ severity: 'warn', summary: 'Đã thu hồi quyền', life: 1200 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: e?.response?.data?.error?.message ?? e.message, life: 3000 })
  } finally {
    togglingId.value = null
  }
}

async function togglePermission(perm) {
  if (!store.selectedRole) return
  if (isGranted(perm.id)) await doRevoke(perm.id)
  else await doGrant(perm.id)
}

// ── Select role ───────────────────────────────────────────────
async function selectRole(role) {
  loadingPerms.value = true
  searchQuery.value = ''
  try {
    await store.fetchRoleDetail(role.id)
  } finally {
    loadingPerms.value = false
  }
}

// ── Init ──────────────────────────────────────────────────────
onMounted(async () => {
  loadingRoles.value = true
  try {
    await Promise.all([store.fetchRoles(), store.fetchPermissions()])
    if (store.roles.length) await selectRole(store.roles[0])
  } finally {
    loadingRoles.value = false
  }
})
</script>

<template>
  <Toast position="top-right" />

  <div class="rm-page">
    <!-- ── Page Header ── -->
    <div class="rm-page__header">
      <div>
        <h1 class="rm-page__title">
          <i class="pi pi-shield mr-2" />
          Phân quyền theo Role
        </h1>
        <p class="rm-page__subtitle">Chọn một Role để xem và chỉnh sửa ma trận quyền tương ứng</p>
      </div>
    </div>

    <div class="rm-layout">
      <!-- ══════════════════════════════════════════════════════
           LEFT: Role list
           ══════════════════════════════════════════════════════ -->
      <aside class="rm-sidebar card">
        <div class="rm-sidebar__head">
          <span class="font-semibold">Danh sách Role</span>
          <span class="rm-sidebar__count">{{ store.roles.length }}</span>
        </div>

        <div v-if="loadingRoles" class="rm-spinner-wrap">
          <ProgressSpinner style="width:28px;height:28px" />
        </div>

        <ul v-else class="rm-role-list">
          <li
            v-for="role in store.roles"
            :key="role.id"
            class="rm-role-item"
            :class="{ 'rm-role-item--active': store.selectedRole?.id === role.id }"
            @click="selectRole(role)"
          >
            <div class="rm-role-item__icon">
              <i class="pi pi-id-card" />
            </div>
            <div class="rm-role-item__body">
              <div class="rm-role-item__name">{{ role.name }}</div>
              <code class="rm-role-item__code">{{ role.code }}</code>
            </div>
            <Tag
              :value="SCOPE_LABELS[role.scope_type] ?? role.scope_type"
              :severity="SCOPE_COLORS[role.scope_type] ?? 'secondary'"
              class="rm-role-item__tag"
            />
          </li>
        </ul>
      </aside>

      <!-- ══════════════════════════════════════════════════════
           RIGHT: Permission matrix
           ══════════════════════════════════════════════════════ -->
      <main class="rm-matrix">
        <!-- Empty state -->
        <div v-if="!store.selectedRole && !loadingRoles" class="rm-empty card">
          <i class="pi pi-arrow-left rm-empty__icon" />
          <p>Chọn một Role để xem quyền</p>
        </div>

        <template v-else-if="store.selectedRole">
          <!-- Role info bar -->
          <div class="card rm-role-bar">
            <div class="rm-role-bar__left">
              <div class="rm-role-bar__name">{{ store.selectedRole.name }}</div>
              <div class="rm-role-bar__meta">
                <code>{{ store.selectedRole.code }}</code>
                <span v-if="store.selectedRole.description" class="rm-role-bar__desc">
                  {{ store.selectedRole.description }}
                </span>
              </div>
            </div>
            <Tag
              :value="SCOPE_LABELS[store.selectedRole.scope_type] ?? store.selectedRole.scope_type"
              :severity="SCOPE_COLORS[store.selectedRole.scope_type] ?? 'secondary'"
            />
            <div class="rm-role-bar__stats">
              <div class="rm-role-bar__stat-label">
                <span class="font-semibold">{{ grantedCount }}</span>
                <span class="text-color-secondary"> / {{ totalCount }} quyền</span>
              </div>
              <div class="rm-progress-track">
                <div class="rm-progress-fill" :style="{ width: grantedPct + '%' }" />
              </div>
              <div class="rm-role-bar__pct">{{ grantedPct }}%</div>
            </div>
          </div>

          <!-- Search -->
          <div class="rm-search">
            <span class="p-input-icon-left rm-search__wrap">
              <i class="pi pi-search" />
              <InputText
                v-model="searchQuery"
                placeholder="Tìm quyền theo tên hoặc mã..."
                class="rm-search__input"
              />
            </span>
            <span v-if="searchQuery" class="rm-search__hint">
              {{ filteredModules.length }} module khớp
            </span>
          </div>

          <!-- Loading perms -->
          <div v-if="loadingPerms" class="rm-spinner-wrap rm-spinner-wrap--lg">
            <ProgressSpinner style="width:40px;height:40px" />
          </div>

          <!-- Module sections -->
          <div v-else class="rm-modules">
            <div
              v-for="mod in filteredModules"
              :key="mod"
              class="rm-module card"
            >
              <!-- Module header -->
              <div class="rm-module__head" @click="toggleModule(mod)">
                <Checkbox
                  :model-value="isModuleAllGranted(mod)"
                  :indeterminate="isModulePartiallyGranted(mod)"
                  binary
                  class="pointer-events-none"
                />
                <i :class="['pi', MODULE_ICONS[mod] ?? 'pi-folder', 'rm-module__icon']" />
                <span class="rm-module__label">{{ MODULE_LABELS[mod] ?? mod }}</span>
                <div class="rm-module__badge">
                  <span
                    class="rm-module__count"
                    :class="{
                      'rm-module__count--full': isModuleAllGranted(mod),
                      'rm-module__count--partial': isModulePartiallyGranted(mod),
                    }"
                  >
                    {{ moduleGrantedCount(mod) }}/{{ filteredPermsByModule[mod]?.length ?? 0 }}
                  </span>
                  <span class="rm-module__toggle-hint">Chọn tất cả</span>
                </div>
              </div>

              <!-- Permission rows -->
              <div class="rm-perm-list">
                <div
                  v-for="perm in filteredPermsByModule[mod]"
                  :key="perm.id"
                  class="rm-perm-row"
                  :class="{ 'rm-perm-row--granted': isGranted(perm.id) }"
                  @click="togglePermission(perm)"
                >
                  <Checkbox
                    :model-value="isGranted(perm.id)"
                    binary
                    class="pointer-events-none rm-perm-row__cb"
                  />
                  <div class="rm-perm-row__info">
                    <div class="rm-perm-row__name">{{ perm.name }}</div>
                    <code class="rm-perm-row__code">{{ perm.code }}</code>
                  </div>
                  <Tag
                    :value="perm.action"
                    :severity="ACTION_COLORS[perm.action] ?? 'secondary'"
                    class="rm-perm-row__action"
                  />
                  <i
                    v-if="togglingId === perm.id"
                    class="pi pi-spin pi-spinner rm-perm-row__spinner"
                  />
                  <i
                    v-else-if="isGranted(perm.id)"
                    class="pi pi-check rm-perm-row__check"
                  />
                </div>
              </div>
            </div>

            <!-- No results -->
            <div v-if="filteredModules.length === 0" class="rm-no-results">
              <i class="pi pi-search rm-no-results__icon" />
              <p>Không tìm thấy quyền phù hợp với "<strong>{{ searchQuery }}</strong>"</p>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── CSS variables: light defaults / dark overrides ─────── */
:global(:root) {
  --rm-surface-subtle:       var(--p-surface-50,  #f9fafb);
  --rm-surface-subtle-hover: var(--p-surface-100, #f3f4f6);
  --rm-icon-bg:              var(--p-surface-100, #f3f4f6);
  --rm-progress-bg:          var(--p-surface-200, #e5e7eb);
  --rm-badge-default-bg:     var(--p-surface-200, #e5e7eb);
  --rm-badge-partial-bg:     #fef3c7;
  --rm-badge-partial-fg:     #92400e;
  --rm-badge-full-bg:        #d1fae5;
  --rm-badge-full-fg:        #065f46;
}

:global(.app-dark) {
  --rm-surface-subtle:       rgba(255, 255, 255, 0.04);
  --rm-surface-subtle-hover: rgba(255, 255, 255, 0.08);
  --rm-icon-bg:              rgba(255, 255, 255, 0.09);
  --rm-progress-bg:          rgba(255, 255, 255, 0.12);
  --rm-badge-default-bg:     rgba(255, 255, 255, 0.1);
  --rm-badge-partial-bg:     rgba(251, 191, 36,  0.18);
  --rm-badge-partial-fg:     #fcd34d;
  --rm-badge-full-bg:        rgba(52,  211, 153, 0.18);
  --rm-badge-full-fg:        #6ee7b7;
}

/* ── Page ─────────────────────────────────────────────────── */
.rm-page {
  padding: 1.5rem;
  min-height: 100%;
}

.rm-page__header {
  margin-bottom: 1.5rem;
}

.rm-page__title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
  display: flex;
  align-items: center;
}

.rm-page__subtitle {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

/* ── Layout ───────────────────────────────────────────────── */
.rm-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.25rem;
  align-items: start;
}

/* ── Sidebar ──────────────────────────────────────────────── */
.rm-sidebar {
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  padding: 1rem;
}

.rm-sidebar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.875rem;
  padding-bottom: 0.625rem;
  border-bottom: 1px solid var(--p-content-border-color);
  font-size: 0.875rem;
}

.rm-sidebar__count {
  background: var(--p-primary-color);
  color: #fff;
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.rm-role-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rm-role-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  border: 1px solid transparent;
}

.rm-role-item:hover {
  background: var(--p-content-hover-background);
  transform: translateX(2px);
}

.rm-role-item--active {
  background: color-mix(in srgb, var(--p-primary-color) 10%, var(--p-content-background));
  border-color: color-mix(in srgb, var(--p-primary-color) 35%, transparent);
  border-left: 3px solid var(--p-primary-color);
}

.rm-role-item__icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--rm-icon-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.875rem;
  color: var(--p-primary-color);
}

.rm-role-item--active .rm-role-item__icon {
  background: var(--p-primary-color);
  color: #fff;
}

.rm-role-item__body {
  flex: 1;
  min-width: 0;
}

.rm-role-item__name {
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rm-role-item__code {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  font-family: monospace;
}

.rm-role-item__tag {
  flex-shrink: 0;
  font-size: 0.65rem;
}

/* ── Matrix area ───────────────────────────────────────────── */
.rm-matrix {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

/* ── Empty state ───────────────────────────────────────────── */
.rm-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  color: var(--p-text-muted-color);
}

.rm-empty__icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  opacity: 0.4;
}

/* ── Role info bar ──────────────────────────────────────────── */
.rm-role-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1rem 1.25rem;
}

.rm-role-bar__left {
  flex: 1;
  min-width: 0;
}

.rm-role-bar__name {
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1.3;
}

.rm-role-bar__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2px;
}

.rm-role-bar__meta code {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  font-family: monospace;
}

.rm-role-bar__desc {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}

.rm-role-bar__stats {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin-left: auto;
}

.rm-role-bar__stat-label {
  font-size: 0.875rem;
  white-space: nowrap;
}

.rm-progress-track {
  width: 100px;
  height: 6px;
  border-radius: 999px;
  background: var(--rm-progress-bg);
  overflow: hidden;
}

.rm-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--p-primary-color);
  transition: width 0.4s ease;
}

.rm-role-bar__pct {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--p-primary-color);
  min-width: 36px;
  text-align: right;
}

/* ── Search ─────────────────────────────────────────────────── */
.rm-search {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.rm-search__wrap {
  flex: 1;
}

.rm-search__input {
  width: 100%;
}

.rm-search__hint {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

/* ── Module card ───────────────────────────────────────────── */
.rm-modules {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.rm-module {
  padding: 0;
  overflow: hidden;
}

.rm-module__head {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  background: var(--rm-surface-subtle);
  border-bottom: 1px solid var(--p-content-border-color);
  transition: background 0.15s;
  user-select: none;
}

.rm-module__head:hover {
  background: var(--rm-surface-subtle-hover);
}

.rm-module__icon {
  color: var(--p-primary-color);
  font-size: 1rem;
  width: 18px;
  text-align: center;
}

.rm-module__label {
  font-weight: 600;
  font-size: 0.875rem;
  flex: 1;
}

.rm-module__badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rm-module__count {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--rm-badge-default-bg);
  color: var(--p-text-muted-color);
}

.rm-module__count--partial {
  background: var(--rm-badge-partial-bg);
  color: var(--rm-badge-partial-fg);
}

.rm-module__count--full {
  background: var(--rm-badge-full-bg);
  color: var(--rm-badge-full-fg);
}

.rm-module__toggle-hint {
  font-size: 0.72rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

/* ── Permission rows ───────────────────────────────────────── */
.rm-perm-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1px;
  background: var(--p-content-border-color);
}

.rm-perm-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.6rem 1rem;
  background: var(--p-content-background);
  cursor: pointer;
  transition: background 0.12s;
  position: relative;
}

.rm-perm-row:hover {
  background: var(--p-content-hover-background);
}

.rm-perm-row--granted {
  background: color-mix(in srgb, var(--p-primary-color) 9%, var(--p-content-background));
}

.rm-perm-row--granted:hover {
  background: color-mix(in srgb, var(--p-primary-color) 15%, var(--p-content-background));
}

.rm-perm-row__cb {
  flex-shrink: 0;
}

.rm-perm-row__info {
  flex: 1;
  min-width: 0;
}

.rm-perm-row__name {
  font-size: 0.8125rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rm-perm-row__code {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  font-family: monospace;
  display: block;
}

.rm-perm-row__action {
  font-size: 0.65rem;
  flex-shrink: 0;
}

.rm-perm-row__spinner {
  font-size: 0.75rem;
  color: var(--p-primary-color);
}

.rm-perm-row__check {
  font-size: 0.7rem;
  color: var(--p-primary-color);
  opacity: 0.6;
}

/* ── No results ─────────────────────────────────────────────── */
.rm-no-results {
  text-align: center;
  padding: 2.5rem;
  color: var(--p-text-muted-color);
}

.rm-no-results__icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
  opacity: 0.35;
}

/* ── Spinner ─────────────────────────────────────────────────── */
.rm-spinner-wrap {
  display: flex;
  justify-content: center;
  padding: 1.5rem;
}

.rm-spinner-wrap--lg {
  padding: 3rem;
}

/* ══════════════════════════════════════════════════════════════
   RESPONSIVE
   ══════════════════════════════════════════════════════════════ */

/* Tablet: collapse sidebar width */
@media (max-width: 1024px) {
  .rm-layout {
    grid-template-columns: 230px 1fr;
  }

  .rm-perm-list {
    grid-template-columns: 1fr;
  }
}

/* Mobile: stack vertically */
@media (max-width: 768px) {
  .rm-page {
    padding: 1rem;
  }

  .rm-layout {
    grid-template-columns: 1fr;
  }

  /* Sidebar becomes horizontal scroll chips */
  .rm-sidebar {
    position: static;
    max-height: none;
    padding: 0.75rem;
    overflow-x: auto;
    overflow-y: visible;
  }

  .rm-sidebar__head {
    display: none;
  }

  .rm-role-list {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 6px;
  }

  .rm-role-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 0.625rem 0.875rem;
    min-width: 90px;
    flex-shrink: 0;
    gap: 4px;
  }

  .rm-role-item:hover {
    transform: none;
  }

  .rm-role-item__icon {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }

  .rm-role-item__code {
    display: none;
  }

  .rm-role-item__tag {
    font-size: 0.6rem;
  }

  .rm-role-bar {
    flex-wrap: wrap;
  }

  .rm-role-bar__stats {
    margin-left: 0;
    width: 100%;
  }

  .rm-progress-track {
    flex: 1;
  }

  .rm-perm-list {
    grid-template-columns: 1fr;
  }

  .rm-module__toggle-hint {
    display: none;
  }
}
</style>
