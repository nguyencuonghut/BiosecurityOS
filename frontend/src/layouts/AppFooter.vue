<script setup></script>

<template>
  <footer class="layout-footer">
    <p class="footer-text">© 2026 Biosecurity OS. All rights reserved.</p>
  </footer>
</template>

<style scoped>
.layout-footer {
  background: var(--p-surface-card);
  border-top: 1px solid var(--p-surface-border);
  padding: 1.5rem;
  text-align: center;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  margin-left: 280px;
  transition: margin-left 0.3s ease;
}

.footer-text {
  margin: 0;
}

.layout-static-inactive .layout-footer {
  margin-left: 60px;
}

@media screen and (max-width: 991px) {
  .layout-footer {
    margin-left: 0;
  }
}
</style>
