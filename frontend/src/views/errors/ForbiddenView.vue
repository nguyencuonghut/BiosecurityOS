<script setup>
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push({ name: 'Dashboard' })
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="error-page">
    <div class="error-wrapper">
      <div class="error-card">
        <!-- Icon Section -->
        <div class="error-icon-wrapper">
          <div class="error-icon">
            <i class="pi pi-lock"></i>
          </div>
        </div>

        <!-- Error Code -->
        <h1 class="error-code">403</h1>

        <!-- Error Title -->
        <h2 class="error-title">Truy cập bị từ chối</h2>

        <!-- Error Description -->
        <p class="error-description">
          Bạn không có quyền để truy cập trang này. Nếu bạn cho rằng đây là lỗi, vui lòng liên hệ với quản trị viên.
        </p>

        <!-- Action Buttons -->
        <div class="error-actions">
          <Button
            label="Về trang chủ"
            icon="pi pi-home"
            @click="goHome"
            severity="primary"
            class="action-button"
          />
          <Button
            label="Quay lại"
            icon="pi pi-arrow-left"
            @click="goBack"
            severity="secondary"
            outlined
            class="action-button"
          />
        </div>

        <!-- Help Text -->
        <p class="error-help">
          Cần giúp đỡ? <a href="mailto:support@biosecurity.local" class="help-link">Liên hệ hỗ trợ</a>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 140px);
  padding: 2rem;
  background: linear-gradient(135deg, var(--p-surface-ground) 0%, var(--p-surface-card) 100%);
  position: relative;
}

.error-page::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--p-red-500), 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.error-wrapper {
  width: 100%;
  max-width: 500px;
  z-index: 1;
}

.error-card {
  padding: 3rem 2.5rem;
  background: var(--p-surface-card);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  text-align: center;
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

/* Icon */
.error-icon-wrapper {
  margin-bottom: 1.5rem;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(var(--p-red-500), 0.2), rgba(var(--p-orange-500), 0.2));
  color: var(--p-red-500);
  font-size: 2.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* Error Code */
.error-code {
  font-size: 3.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: var(--p-red-500);
  line-height: 1;
}

/* Error Title */
.error-title {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0 0 1rem;
  color: var(--p-text-color);
}

/* Error Description */
.error-description {
  margin: 0 0 2rem;
  font-size: 1rem;
  color: var(--p-text-muted-color);
  line-height: 1.6;
}

/* Action Buttons */
.error-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  justify-content: center;
  flex-wrap: wrap;
}

.action-button {
  min-width: 160px;
}

/* Help Text */
.error-help {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin: 0;
  padding-top: 1.5rem;
  border-top: 1px solid var(--p-surface-border);
}

.help-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.help-link:hover {
  color: var(--p-primary-600);
  text-decoration: underline;
}

/* Responsive */
@media screen and (max-width: 768px) {
  .error-page {
    min-height: calc(100vh - 120px);
    padding: 1.5rem;
  }

  .error-card {
    padding: 2rem 1.5rem;
    border-radius: 12px;
  }

  .error-code {
    font-size: 2.5rem;
  }

  .error-title {
    font-size: 1.5rem;
  }

  .error-icon {
    width: 70px;
    height: 70px;
    font-size: 2rem;
  }

  .error-actions {
    flex-direction: column;
  }

  .action-button {
    min-width: auto;
  }
}
</style>
