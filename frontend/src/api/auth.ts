import api from './index'
import type { ApiResponse, TokenResponse, User } from '../types'

export function login(username: string, password: string) {
  return api.post<ApiResponse<TokenResponse>>('/auth/login', { username, password })
}

export function logout() {
  return api.post<ApiResponse<any>>('/auth/logout')
}

export function getUsers() {
  return api.get<ApiResponse<User[]>>('/users')
}

export function createUser(data: { username: string; password: string; global_role: string }) {
  return api.post<ApiResponse<User>>('/users', data)
}

export function updateUser(id: string, data: { global_role: string }) {
  return api.put<ApiResponse<User>>(`/users/${id}`, data)
}

export function deleteUser(id: string) {
  return api.delete<ApiResponse<any>>(`/users/${id}`)
}

export function getCurrentUser() {
  return api.get<ApiResponse<User>>('/auth/me')
}
