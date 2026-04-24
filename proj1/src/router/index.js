import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/Projects.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/environments',
    name: 'Environments',
    component: () => import('../views/Environments.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('../views/Models.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/env-gen',
    name: 'EnvGen',
    component: () => import('../views/EnvGen.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'config', 'dev'] }
  },
  {
    path: '/env-adjust',
    name: 'EnvAdjust',
    component: () => import('../views/EnvAdjust.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'config', 'dev'] }
  },
  {
    path: '/env-optimize',
    name: 'EnvOptimize',
    component: () => import('../views/EnvOptimize.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'config', 'dev'] }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('role')

  if (requiresAuth && !token) {
    next({ name: 'Login' })
  } else if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
