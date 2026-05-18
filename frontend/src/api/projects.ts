import api from './index'
import type { ApiResponse, Project } from '../types'

export function getProjects(params?: { page?: number; page_size?: number }) {
  return api.get<ApiResponse<Project[]>>('/projects', { params })
}

export function getProject(id: string) {
  return api.get<ApiResponse<Project>>(`/projects/${id}`)
}

export function createProject(data: Partial<Project>) {
  return api.post<ApiResponse<Project>>('/projects', data)
}

export function updateProject(id: string, data: Partial<Project>) {
  return api.put<ApiResponse<Project>>(`/projects/${id}`, data)
}

export function deleteProject(id: string) {
  return api.delete<ApiResponse<any>>(`/projects/${id}`)
}

export function getMembers(projectId: string) {
  return api.get<ApiResponse<any[]>>(`/projects/${projectId}/members`)
}

export function addMember(projectId: string, data: { user_id: string; role: string }) {
  return api.post<ApiResponse<any>>(`/projects/${projectId}/members`, data)
}

export function removeMember(projectId: string, userId: string) {
  return api.delete<ApiResponse<any>>(`/projects/${projectId}/members/${userId}`)
}
