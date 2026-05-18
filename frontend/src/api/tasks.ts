import api from './index'
import type { ApiResponse, PaginatedResponse, Task } from '../types'

export function getTasks(projectId: string, params?: { page?: number; page_size?: number }) {
  return api.get<ApiResponse<PaginatedResponse<Task>>>(`/projects/${projectId}/tasks`, { params })
}

export function getTask(projectId: string, id: string) {
  return api.get<ApiResponse<Task>>(`/projects/${projectId}/tasks/${id}`)
}

export function createTask(projectId: string, data: Partial<Task>) {
  return api.post<ApiResponse<Task>>(`/projects/${projectId}/tasks`, data)
}

export function updateTask(projectId: string, id: string, data: Partial<Task>) {
  return api.put<ApiResponse<Task>>(`/projects/${projectId}/tasks/${id}`, data)
}

export function deleteTask(projectId: string, id: string) {
  return api.delete<ApiResponse<any>>(`/projects/${projectId}/tasks/${id}`)
}
