<script setup>
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="notfound-container">
    <div class="notfound-card">
      <i class="pi pi-search" style="font-size: 3rem; color: var(--p-orange-500)"></i>
      <h1>404</h1>
      <p>Trang bạn tìm không tồn tại.</p>
      <Button label="Về trang chủ" icon="pi pi-home" @click="router.push('/')" />
    </div>
  </div>
</template>

<style scoped>
.notfound-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.notfound-card {
  text-align: center;
  padding: 3rem;
}

.notfound-card h1 {
  font-size: 3rem;
  margin: 1rem 0 0.5rem;
  color: var(--p-text-color);
}

.notfound-card p {
  margin-bottom: 1.5rem;
  color: var(--p-text-muted-color);
}
</style>
