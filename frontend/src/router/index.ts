import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/envs',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'envs',
        name: 'Envs',
        component: () => import('@/views/Envs.vue'),
        meta: { title: '环境管理' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/Monitor.vue'),
        meta: { title: '训练监控' }
      },
      {
        path: 'optimization',
        name: 'Optimization',
        component: () => import('@/views/Optimization.vue'),
        meta: { title: '优化中心' }
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/Models.vue'),
        meta: { title: '模型库' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
