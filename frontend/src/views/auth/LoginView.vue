<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  try {
    await authStore.login(username.value, password.value)
    router.push({ name: 'Dashboard' })
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMsg.value = detail
    } else if (detail?.message) {
      errorMsg.value = detail.message
    } else {
      errorMsg.value = 'Đăng nhập thất bại. Vui lòng thử lại.'
    }
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <i class="pi pi-shield" style="font-size: 2.5rem; color: var(--p-primary-color)"></i>
        <h1>BIOSECURITY OS</h1>
        <p class="login-subtitle">Hệ thống quản lý an toàn sinh học</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <Message v-if="errorMsg" severity="error" :closable="false" class="login-error">
          {{ errorMsg }}
        </Message>

        <div class="field">
          <label for="username">Tên đăng nhập</label>
          <InputText
            id="username"
            v-model="username"
            placeholder="Nhập tên đăng nhập"
            :fluid="true"
            autocomplete="username"
          />
        </div>

        <div class="field">
          <label for="password">Mật khẩu</label>
          <Password
            id="password"
            v-model="password"
            placeholder="Nhập mật khẩu"
            :feedback="false"
            :toggleMask="true"
            :fluid="true"
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </div>

        <Button
          type="submit"
          label="Đăng nhập"
          icon="pi pi-sign-in"
          :loading="authStore.loading"
          :fluid="true"
        />
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--p-surface-ground);
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  border-radius: 12px;
  background: var(--p-surface-card);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  margin: 0.5rem 0 0.25rem;
  font-size: 1.5rem;
  color: var(--p-text-color);
}

.login-subtitle {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--p-text-color);
}

.login-error {
  margin: 0;
}
</style>
