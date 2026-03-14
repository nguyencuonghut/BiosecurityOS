import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/ExecutiveDashboard.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Route guard — will be enhanced with real auth check in auth module
router.beforeEach((to) => {
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && isAuthenticated) {
    return { name: 'Dashboard' }
  }
})

export default router
