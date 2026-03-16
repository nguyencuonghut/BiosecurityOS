<script setup>
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import Tree from 'primevue/tree'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import InputSwitch from 'primevue/inputswitch'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useFarmStore } from '@/stores/farm.js'
import { useAuthStore } from '@/stores/auth.js'

const props = defineProps({
  farmId: { type: String, required: true },
})

const toast = useToast()
const farmStore = useFarmStore()
const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermission('FARM_WRITE'))

const showDialog = ref(false)
const editArea = ref(null)
const saving = ref(false)
const errorMsg = ref('')

const form = ref({
  code: '',
  name: '',
  area_type: '',
  parent_area_id: null,
  clean_dirty_class: null,
  is_active: true,
})

const areaTypeOptions = [
  { label: 'Cổng', value: 'gate' },
  { label: 'Chuồng', value: 'barn' },
  { label: 'Kho', value: 'storage' },
  { label: 'Văn phòng', value: 'office' },
  { label: 'Sân', value: 'yard' },
  { label: 'Đệm', value: 'buffer_zone' },
  { label: 'Khác', value: 'other' },
]

const cleanDirtyOptions = [
  { label: '— Chưa phân loại —', value: null },
  { label: 'Sạch', value: 'clean' },
  { label: 'Đệm', value: 'buffer' },
  { label: 'Bẩn', value: 'dirty' },
]

// Build tree nodes from flat areas
const treeNodes = computed(() => {
  const areas = farmStore.areas
  const idMap = {}
  const roots = []

  areas.forEach((a) => {
    idMap[a.id] = {
      key: a.id,
      label: `${a.code} — ${a.name}`,
      data: a,
      children: [],
    }
  })

  areas.forEach((a) => {
    if (a.parent_area_id && idMap[a.parent_area_id]) {
      idMap[a.parent_area_id].children.push(idMap[a.id])
    } else {
      roots.push(idMap[a.id])
    }
  })

  return roots
})

const parentOptions = computed(() => {
  const opts = [{ label: '— Gốc (không cha) —', value: null }]
  farmStore.areas.forEach((a) => {
    if (editArea.value && a.id === editArea.value.id) return // don't self-parent
    opts.push({ label: `${a.code} — ${a.name}`, value: a.id })
  })
  return opts
})

function openCreate(parentId = null) {
  editArea.value = null
  form.value = {
    code: '',
    name: '',
    area_type: '',
    parent_area_id: parentId,
    clean_dirty_class: null,
    is_active: true,
  }
  errorMsg.value = ''
  showDialog.value = true
}

function openEdit(area) {
  editArea.value = area
  form.value = {
    code: area.code,
    name: area.name,
    area_type: area.area_type,
    parent_area_id: area.parent_area_id,
    clean_dirty_class: area.clean_dirty_class,
    is_active: area.is_active,
  }
  errorMsg.value = ''
  showDialog.value = true
}

async function onSubmit() {
  errorMsg.value = ''
  if (!form.value.name?.trim() || !form.value.area_type) {
    errorMsg.value = 'Vui lòng nhập Tên và Loại khu vực.'
    return
  }
  if (!editArea.value && !form.value.code?.trim()) {
    errorMsg.value = 'Vui lòng nhập Mã khu vực.'
    return
  }

  saving.value = true
  try {
    const payload = { ...form.value }
    if (editArea.value) {
      delete payload.code
      await farmStore.saveArea(props.farmId, payload, editArea.value.id)
    } else {
      await farmStore.saveArea(props.farmId, payload)
    }
    showDialog.value = false
    toast.add({ severity: 'success', summary: 'Thành công', detail: 'Đã lưu khu vực', life: 3000 })
  } catch (err) {
    errorMsg.value = err.response?.data?.error?.message || 'Lỗi khi lưu khu vực.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="area-panel">
    <div class="panel-header">
      <span class="panel-title">Cây khu vực</span>
      <Button
        v-if="canWrite"
        label="Thêm khu vực"
        icon="pi pi-plus"
        size="small"
        @click="openCreate()"
      />
    </div>

    <Tree
      :value="treeNodes"
      class="area-tree"
      v-if="treeNodes.length"
    >
      <template #default="{ node }">
        <div class="tree-node-content">
          <span class="node-label">{{ node.label }}</span>
          <span class="node-badges">
            <StatusBadge v-if="node.data.clean_dirty_class" :value="node.data.clean_dirty_class" type="clean_dirty" />
            <span v-if="!node.data.is_active" class="inactive-text">Không hoạt động</span>
          </span>
          <span class="node-actions" v-if="canWrite">
            <Button icon="pi pi-plus" text rounded size="small" severity="secondary" v-tooltip.top="'Thêm con'" @click.stop="openCreate(node.key)" />
            <Button icon="pi pi-pencil" text rounded size="small" severity="secondary" v-tooltip.top="'Sửa'" @click.stop="openEdit(node.data)" />
          </span>
        </div>
      </template>
    </Tree>

    <div v-else class="empty-msg">Chưa có khu vực nào.</div>

    <!-- Create/Edit dialog -->
    <Dialog
      :visible="showDialog"
      :header="editArea ? 'Sửa khu vực' : 'Thêm khu vực'"
      modal
      :style="{ width: '30rem' }"
      @update:visible="showDialog = $event"
    >
      <div class="form-fields" v-if="showDialog">
        <div class="field" v-if="!editArea">
          <label>Mã *</label>
          <InputText v-model="form.code" placeholder="VD: GATE-01" :fluid="true" />
        </div>
        <div class="field">
          <label>Tên *</label>
          <InputText v-model="form.name" placeholder="Tên khu vực" :fluid="true" />
        </div>
        <div class="field">
          <label>Loại *</label>
          <Select v-model="form.area_type" :options="areaTypeOptions" optionLabel="label" optionValue="value" placeholder="Chọn loại" :fluid="true" />
        </div>
        <div class="field">
          <label>Khu vực cha</label>
          <Select v-model="form.parent_area_id" :options="parentOptions" optionLabel="label" optionValue="value" :fluid="true" />
        </div>
        <div class="field">
          <label>Phân vùng sạch/bẩn</label>
          <Select v-model="form.clean_dirty_class" :options="cleanDirtyOptions" optionLabel="label" optionValue="value" :fluid="true" />
        </div>
        <div class="field-row">
          <label>Hoạt động</label>
          <InputSwitch v-model="form.is_active" />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      </div>

      <template #footer>
        <Button label="Hủy" severity="secondary" text @click="showDialog = false" />
        <Button :label="editArea ? 'Cập nhật' : 'Tạo'" icon="pi pi-check" :loading="saving" @click="onSubmit" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.panel-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.area-tree {
  border: none;
  padding: 0;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.node-label {
  font-weight: 500;
}

.node-badges {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.inactive-text {
  font-size: 0.75rem;
  color: var(--p-red-500);
}

.node-actions {
  margin-left: auto;
  display: flex;
  gap: 0;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field label {
  font-weight: 600;
  font-size: 0.85rem;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.field-row label {
  font-weight: 600;
  font-size: 0.85rem;
}

.error-msg {
  color: var(--p-red-500);
  font-size: 0.85rem;
}

.empty-msg {
  text-align: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
}
</style>
