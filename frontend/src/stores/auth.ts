import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '../api/auth'
import type { User } from '../types'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    const data = res.data.data || res.data
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
    router.push('/')
  }

  async function fetchUser() {
    try {
      const res = await getCurrentUser()
      user.value = res.data.data || res.data
    } catch {
      user.value = null
    }
  }

  async function logout() {
    try { await apiLogout() } catch {}
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  return { token, user, login, logout, fetchUser }
})
