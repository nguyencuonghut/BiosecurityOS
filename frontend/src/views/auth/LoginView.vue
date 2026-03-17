<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Checkbox from 'primevue/checkbox'
import { useAuthStore } from '@/stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const errorMsg = ref('')
const isLoading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  isLoading.value = true
  try {
    await authStore.login(username.value, password.value)
    if (rememberMe.value) {
      localStorage.setItem('biosec_remember_user', username.value)
    } else {
      localStorage.removeItem('biosec_remember_user')
    }
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
  } finally {
    isLoading.value = false
  }
}

// Load saved username if "Remember me" was checked before
const savedUser = localStorage.getItem('biosec_remember_user')
if (savedUser) {
  username.value = savedUser
  rememberMe.value = true
}
</script>

<template>
  <div class="login-page">
    <div class="login-wrapper">
      <div class="login-card">
        <!-- Brand Section -->
        <div class="login-brand">
          <div class="brand-logo">
            <i class="pi pi-shield"></i>
          </div>
          <h1 class="brand-title">Biosecurity OS</h1>
          <p class="brand-subtitle">Hệ thống quản lý an toàn sinh học</p>
        </div>

        <!-- Error Message -->
        <Message 
          v-if="errorMsg" 
          severity="error" 
          :text="errorMsg"
          class="login-error-msg"
        />

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-field">
            <label for="username" class="field-label">Tên đăng nhập</label>
            <InputText
              id="username"
              v-model="username"
              placeholder="admin"
              :fluid="true"
              autocomplete="username"
              :disabled="isLoading"
              class="form-input"
            />
          </div>

          <div class="form-field">
            <label for="password" class="field-label">Mật khẩu</label>
            <Password
              id="password"
              v-model="password"
              placeholder="••••••••"
              :feedback="false"
              :toggleMask="true"
              :fluid="true"
              autocomplete="current-password"
              :disabled="isLoading"
              @keyup.enter="handleLogin"
              class="form-input"
              inputClass="password-input"
            />
          </div>

          <div class="form-options">
            <div class="checkbox-wrapper">
              <Checkbox 
                v-model="rememberMe" 
                inputId="rememberMe"
                :disabled="isLoading"
              />
              <label for="rememberMe" class="checkbox-label">Ghi nhớ tôi</label>
            </div>
          </div>

          <Button
            type="submit"
            label="Đăng nhập"
            icon="pi pi-sign-in"
            :loading="isLoading"
            :fluid="true"
            class="login-button"
          />
        </form>

        <!-- Footer -->
        <div class="login-footer">
          <p class="footer-text">© 2026 Biosecurity OS. All rights reserved.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--p-surface-ground) 0%, var(--p-surface-card) 100%);
  position: relative;
  overflow: hidden;
}

/* Background decoration */
.login-page::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--p-primary-500), 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.login-page::after {
  content: '';
  position: absolute;
  bottom: -20%;
  left: -5%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--p-primary-500), 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 2rem;
  z-index: 1;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 3rem;
  background: var(--p-surface-card);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Brand Section */
.login-brand {
  text-align: center;
  margin-bottom: 2.5rem;
}

.brand-logo {
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--p-primary-color), var(--p-primary-600));
  border-radius: 16px;
  font-size: 2.5rem;
  color: var(--p-primary-contrast-color);
  animation: bounce 0.6s ease-out;
}

@keyframes bounce {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.brand-title {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--p-text-color);
  letter-spacing: -0.5px;
}

.brand-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: var(--p-text-muted-color);
  font-weight: 500;
}

/* Error Message */
.login-error-msg {
  margin-bottom: 1.5rem;
  animation: shake 0.3s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-text-color);
  letter-spacing: 0.3px;
}

.form-input {
  transition: all 0.2s ease;
}

.form-input:focus {
  box-shadow: 0 0 0 3px rgba(var(--p-primary-500), 0.1);
}

.password-input {
  font-family: 'Courier New', monospace;
}

/* Form Options */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label {
  cursor: pointer;
  color: var(--p-text-color);
  user-select: none;
}

/* Login Button */
.login-button {
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.3px;
  height: 44px;
}

/* Footer */
.login-footer {
  text-align: center;
  padding-top: 1.5rem;
  border-top: 1px solid var(--p-surface-border);
}

.footer-text {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

/* Responsive */
@media screen and (max-width: 640px) {
  .login-wrapper {
    padding: 1rem;
  }

  .login-card {
    padding: 2rem;
    border-radius: 12px;
  }

  .brand-logo {
    width: 60px;
    height: 60px;
    font-size: 2rem;
  }

  .brand-title {
    font-size: 1.5rem;
  }

  .login-form {
    gap: 1rem;
  }

  .login-page::before,
  .login-page::after {
    display: none;
  }
}
</style>
