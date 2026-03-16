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
      {
        path: 'scorecards',
        name: 'Scorecards',
        component: () => import('@/views/scorecards/ScorecardListView.vue'),
        meta: { permission: 'SCORECARD_READ' },
      },
      {
        path: 'scorecards/:id',
        name: 'ScorecardBuilder',
        component: () => import('@/views/scorecards/ScorecardBuilderView.vue'),
        meta: { permission: 'SCORECARD_READ' },
      },
      {
        path: 'assessments',
        name: 'Assessments',
        component: () => import('@/views/assessments/AssessmentListView.vue'),
        meta: { permission: 'ASSESSMENT_READ' },
      },
      {
        path: 'assessments/:id',
        name: 'AssessmentForm',
        component: () => import('@/views/assessments/AssessmentFormView.vue'),
        meta: { permission: 'ASSESSMENT_READ' },
      },
      {
        path: 'killer-metrics/definitions',
        name: 'KillerMetricDefinitions',
        component: () => import('@/views/killer-metrics/KillerMetricDefinitionAdmin.vue'),
        meta: { permission: 'KILLER_EVENT_WRITE' },
      },
      {
        path: 'killer-metrics/events',
        name: 'KillerMetricEvents',
        component: () => import('@/views/killer-metrics/KillerMetricEventList.vue'),
        meta: { permission: 'KILLER_EVENT_READ' },
      },
      {
        path: 'cases',
        name: 'CaseQueue',
        component: () => import('@/views/cases/CaseQueueView.vue'),
        meta: { permission: 'CASE_CREATE' },
      },
      {
        path: 'cases/:id',
        name: 'CaseDetail',
        component: () => import('@/views/cases/CaseDetailView.vue'),
        meta: { permission: 'CASE_CREATE' },
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
