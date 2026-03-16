<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'
import StatusBadge from '@/components/common/StatusBadge.vue'
import UserRoleDialog from '@/views/admin/UserRoleDialog.vue'
import { useUserStore } from '@/stores/user.js'
import { useFarmStore } from '@/stores/farm.js'

const toast = useToast()
const userStore = useUserStore()
const farmStore = useFarmStore()

const showUserDialog = ref(false)
const showRoleDialog = ref(false)
const editUser = ref(null)
const selectedUserId = ref(null)
const saving = ref(false)
const errorMsg = ref('')
const statusFilter = ref(null)

const statusOptions = [
  { label: 'Tất cả', value: null },
  { label: 'Hoạt động', value: 'active' },
  { label: 'Khóa', value: 'locked' },
  { label: 'Lưu trữ', value: 'archived' },
]

const form = ref({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  region_id: null,
  farm_id: null,
  title: '',
  status: 'active',
  password: '',
})

onMounted(async () => {
  await farmStore.fetchRegions()
  await userStore.fetchUsers()
})

watch(statusFilter, () => {
  userStore.filters.status = statusFilter.value
  userStore.filters.page = 1
  userStore.fetchUsers()
})

function onPage(event) {
  userStore.filters.page = event.page + 1
  userStore.filters.page_size = event.rows
  userStore.fetchUsers()
}

function onSort(event) {
  const prefix = event.sortOrder === -1 ? '-' : ''
  userStore.filters.sort = prefix + event.sortField
  userStore.fetchUsers()
}

function openCreate() {
  editUser.value = null
  form.value = { username: '', full_name: '', email: '', phone: '', region_id: null, farm_id: null, title: '', status: 'active', password: '' }
  errorMsg.value = ''
  showUserDialog.value = true
}

function openEdit(user) {
  editUser.value = user
  form.value = {
    username: user.username,
    full_name: user.full_name,
    email: user.email || '',
    phone: user.phone || '',
    region_id: user.region_id,
    farm_id: user.farm_id,
    title: user.title || '',
    status: user.status,
    password: '',
  }
  errorMsg.value = ''
  showUserDialog.value = true
}

function openRoles(user) {
  selectedUserId.value = user.id
  showRoleDialog.value = true
}

async function onSubmitUser() {
  errorMsg.value = ''
  if (!form.value.full_name?.trim()) {
    errorMsg.value = 'Vui lòng nhập Họ tên.'
    return
  }
  if (!editUser.value && (!form.value.username?.trim() || !form.value.password)) {
    errorMsg.value = 'Vui lòng nhập Tên đăng nhập và Mật khẩu.'
    return
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.email) delete payload.email
    if (!payload.phone) delete payload.phone
    if (!payload.title) delete payload.title
    if (!payload.region_id) delete payload.region_id
    if (!payload.farm_id) delete payload.farm_id

    if (editUser.value) {
      delete payload.username
      if (!payload.password) delete payload.password
      await userStore.saveUser(payload, editUser.value.id)
    } else {
      await userStore.saveUser(payload)
    }
    showUserDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã lưu người dùng', life: 3000 })
    await userStore.fetchUsers()
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Lỗi khi lưu người dùng.'
  } finally {
    saving.value = false
  }
}

function regionName(id) {
  if (!id) return '—'
  const r = farmStore.regions.find((r) => r.id === id)
  return r?.name || '—'
}

function rolesList(user) {
  if (!user.roles?.length) return '—'
  return user.roles.map((r) => r.role_code || r.role_name).join(', ')
}

async function onRolesUpdated() {
  await userStore.fetchUsers()
}
</script>

<template>
  <Toast />
  <div class="user-mgmt">
    <div class="page-header">
      <h2>Quản lý người dùng</h2>
      <Button label="Thêm người dùng" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable
      :value="userStore.users"
      :totalRecords="userStore.totalRecords"
      :loading="userStore.loading"
      :rows="userStore.filters.page_size"
      :rowsPerPageOptions="[10, 20, 50]"
      paginator
      lazy
      stripedRows
      removableSort
      @page="onPage"
      @sort="onSort"
    >
      <template #header>
        <div class="filter-bar">
          <Select
            v-model="statusFilter"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Trạng thái"
            style="min-width: 10rem"
          />
        </div>
      </template>

      <Column field="username" header="Tên đăng nhập" sortable style="width: 10rem" />
      <Column field="full_name" header="Họ tên" sortable style="min-width: 12rem" />
      <Column field="email" header="Email" sortable style="min-width: 14rem">
        <template #body="{ data }">{{ data.email || '—' }}</template>
      </Column>
      <Column header="Vùng" style="width: 8rem">
        <template #body="{ data }">{{ regionName(data.region_id) }}</template>
      </Column>
      <Column header="Vai trò" style="min-width: 12rem">
        <template #body="{ data }">
          <div class="roles-cell">
            <Tag v-for="r in (data.roles || [])" :key="r.id" :value="r.role_code" severity="info" rounded class="role-tag" />
            <span v-if="!data.roles?.length" class="text-muted">—</span>
          </div>
        </template>
      </Column>
      <Column field="status" header="Trạng thái" sortable style="width: 8rem">
        <template #body="{ data }">
          <StatusBadge :value="data.status" type="status" />
        </template>
      </Column>
      <Column style="width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text rounded severity="secondary" v-tooltip.top="'Sửa'" @click="openEdit(data)" />
          <Button icon="pi pi-shield" text rounded severity="secondary" v-tooltip.top="'Vai trò'" @click="openRoles(data)" />
        </template>
      </Column>

      <template #empty>
        <div class="empty-msg">Không có người dùng nào.</div>
      </template>
    </DataTable>

    <!-- User create/edit dialog -->
    <Dialog
      :visible="showUserDialog"
      :header="editUser ? 'Chỉnh sửa người dùng' : 'Thêm người dùng'"
      modal
      :style="{ width: '34rem' }"
      @update:visible="showUserDialog = $event"
    >
      <Message v-if="errorMsg" severity="error" :closable="false" class="mb-3">{{ errorMsg }}</Message>
      <div class="form-grid">
        <div class="field" v-if="!editUser">
          <label>Tên đăng nhập *</label>
          <InputText v-model="form.username" :fluid="true" />
        </div>
        <div class="field">
          <label>Họ tên *</label>
          <InputText v-model="form.full_name" :fluid="true" />
        </div>
        <div class="field">
          <label>Email</label>
          <InputText v-model="form.email" type="email" :fluid="true" />
        </div>
        <div class="field">
          <label>Điện thoại</label>
          <InputText v-model="form.phone" :fluid="true" />
        </div>
        <div class="field">
          <label>Vùng</label>
          <Select v-model="form.region_id" :options="farmStore.regions" optionLabel="name" optionValue="id" placeholder="Chọn vùng" :fluid="true" showClear />
        </div>
        <div class="field">
          <label>Chức danh</label>
          <InputText v-model="form.title" :fluid="true" />
        </div>
        <div class="field">
          <label>Trạng thái</label>
          <Select v-model="form.status" :options="statusOptions.filter(o => o.value)" optionLabel="label" optionValue="value" :fluid="true" />
        </div>
        <div class="field">
          <label>{{ editUser ? 'Mật khẩu mới (bỏ trống = giữ nguyên)' : 'Mật khẩu *' }}</label>
          <Password v-model="form.password" :feedback="false" :toggleMask="true" :fluid="true" />
        </div>
      </div>

      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showUserDialog = false" />
        <Button :label="editUser ? 'Cập nhật' : 'Tạo'" icon="pi pi-check" :loading="saving" @click="onSubmitUser" />
      </template>
    </Dialog>

    <!-- Role assignment dialog -->
    <UserRoleDialog
      v-model:visible="showRoleDialog"
      :userId="selectedUserId"
      @updated="onRolesUpdated"
    />
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.page-header h2 { margin: 0; font-size: 1.25rem; }
.filter-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
.field label { font-weight: 600; font-size: 0.85rem; }
.roles-cell { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.role-tag { font-size: 0.75rem; }
.text-muted { color: var(--p-text-muted-color); }
.empty-msg { text-align: center; padding: 2rem; color: var(--p-text-muted-color); }
.mb-3 { margin-bottom: 0.75rem; }
</style>
