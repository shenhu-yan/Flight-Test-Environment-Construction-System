import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

interface User {
  id: string
  username: string
  global_role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const response = await api.post('/api/auth/login', { username, password })
    token.value = response.data.access_token
    localStorage.setItem('token', response.data.access_token)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data.data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    fetchUser,
    logout
  }
})
