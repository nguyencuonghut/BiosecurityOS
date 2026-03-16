<script setup>
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="forbidden-container">
    <div class="forbidden-card">
      <i class="pi pi-lock" style="font-size: 3rem; color: var(--p-red-500)"></i>
      <h1>403</h1>
      <p>Bạn không có quyền truy cập trang này.</p>
      <Button label="Về trang chủ" icon="pi pi-home" @click="router.push('/')" />
    </div>
  </div>
</template>

<style scoped>
.forbidden-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.forbidden-card {
  text-align: center;
  padding: 3rem;
}

.forbidden-card h1 {
  font-size: 3rem;
  margin: 1rem 0 0.5rem;
  color: var(--p-text-color);
}

.forbidden-card p {
  margin-bottom: 1.5rem;
  color: var(--p-text-muted-color);
}
</style>
