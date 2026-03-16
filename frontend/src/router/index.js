import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/errors/ForbiddenView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/ExecutiveDashboard.vue'),
      },
      {
        path: 'farms',
        name: 'Farms',
        component: () => import('@/views/farms/FarmListView.vue'),
        meta: { permission: 'FARM_READ' },
      },
      {
        path: 'farms/:id',
        name: 'FarmDetail',
        component: () => import('@/views/farms/FarmDetailView.vue'),
        meta: { permission: 'FARM_READ' },
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: () => import('@/views/admin/UserManagementView.vue'),
        meta: { permission: 'USER_ADMIN' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/errors/NotFoundView.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── Route guard — uses auth store (lazy import to avoid circular deps) ──
router.beforeEach(async (to) => {
  // Lazy import to avoid circular dependency with store ↔ router
  const { useAuthStore } = await import('@/stores/auth.js')
  const authStore = useAuthStore()

  // If authenticated but profile not yet loaded (page refresh), fetch it
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.init()
    } catch {
      return { name: 'Login' }
    }
  }

  // Check authentication
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  // Redirect logged-in users away from login page
  if (to.name === 'Login' && authStore.isAuthenticated) {
    return { name: 'Dashboard' }
  }

  // Check route-level permission
  if (to.meta.permission && !authStore.hasPermission(to.meta.permission)) {
    return { name: 'Forbidden' }
  }
})

export default router
