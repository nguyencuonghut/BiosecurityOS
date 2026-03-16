<script setup>
import { ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import * as userService from '@/services/userService.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  userId: { type: String, default: null },
})

const emit = defineEmits(['update:visible', 'updated'])

const toast = useToast()
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')

const user = ref(null)
const allRoles = ref([])
const selectedRoleId = ref(null)

async function loadData() {
  if (!props.userId) return
  loading.value = true
  errorMsg.value = ''
  try {
    const [userData, rolesData] = await Promise.all([
      userService.getUser(props.userId),
      userService.listRoles(),
    ])
    user.value = userData
    allRoles.value = rolesData
  } catch (err) {
    errorMsg.value = 'Không thể tải dữ liệu.'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val && props.userId) {
      selectedRoleId.value = null
      loadData()
    }
  },
)

async function onAssign() {
  if (!selectedRoleId.value) return
  saving.value = true
  errorMsg.value = ''
  try {
    await userService.assignRole(props.userId, { role_id: selectedRoleId.value })
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã gán vai trò', life: 3000 })
    selectedRoleId.value = null
    await loadData()
    emit('updated')
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Lỗi khi gán vai trò.'
  } finally {
    saving.value = false
  }
}

async function onRemove(userRoleId) {
  try {
    await userService.removeRole(props.userId, userRoleId)
    toast.add({ severity: 'info', summary: 'Đã gỡ', detail: 'Đã gỡ vai trò', life: 3000 })
    await loadData()
    emit('updated')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Lỗi', detail: err.response?.data?.error?.message || 'Lỗi', life: 3000 })
  }
}

function onHide() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    header="Quản lý vai trò"
    modal
    :style="{ width: '36rem' }"
    @update:visible="onHide"
  >
    <div v-if="loading" class="loading-msg">
      <i class="pi pi-spin pi-spinner"></i> Đang tải...
    </div>

    <div v-else-if="user">
      <p class="user-info">
        <strong>{{ user.full_name }}</strong> ({{ user.username }})
      </p>

      <Message v-if="errorMsg" severity="error" :closable="false" class="mb-3">{{ errorMsg }}</Message>

      <!-- Current roles -->
      <div class="section-title">Vai trò hiện tại</div>
      <DataTable :value="user.roles || []" stripedRows class="mb-3" v-if="user.roles?.length">
        <Column header="Vai trò">
          <template #body="{ data }">
            <Tag :value="data.role_code" severity="info" rounded />
            <span class="ml-2">{{ data.role_name }}</span>
          </template>
        </Column>
        <Column header="Scope" style="width: 10rem">
          <template #body="{ data }">
            <span v-if="data.scope_region_id">Region</span>
            <span v-else-if="data.scope_farm_id">Farm</span>
            <span v-else>Global</span>
          </template>
        </Column>
        <Column style="width: 4rem">
          <template #body="{ data }">
            <Button icon="pi pi-trash" text rounded severity="danger" size="small" v-tooltip.top="'Gỡ'" @click="onRemove(data.id)" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="empty-msg mb-3">Chưa có vai trò nào.</div>

      <!-- Assign new role -->
      <div class="section-title">Gán vai trò mới</div>
      <div class="assign-row">
        <Select
          v-model="selectedRoleId"
          :options="allRoles"
          optionLabel="name"
          optionValue="id"
          placeholder="Chọn vai trò"
          class="assign-select"
        />
        <Button label="Gán" icon="pi pi-plus" :loading="saving" :disabled="!selectedRoleId" @click="onAssign" />
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.user-info {
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.section-title {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.assign-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}
.assign-select {
  flex: 1;
}
.loading-msg {
  text-align: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
}
.empty-msg {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}
.mb-3 { margin-bottom: 0.75rem; }
.ml-2 { margin-left: 0.5rem; }
</style>
