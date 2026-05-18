import api from './index'
import type { ApiResponse, Template, EnvConfig } from '../types'

export function getTemplates(params?: { aircraft_type?: string; difficulty?: string }) {
  return api.get<ApiResponse<Template[]>>('/templates', { params })
}

export function getTemplate(id: string) {
  return api.get<ApiResponse<Template>>(`/templates/${id}`)
}

export function createTemplate(data: { name: string; aircraft_type: string; difficulty: string; config: EnvConfig }) {
  return api.post<ApiResponse<Template>>('/templates', data)
}

export function updateTemplate(id: string, data: Partial<Template>) {
  return api.put<ApiResponse<Template>>(`/templates/${id}`, data)
}

export function deleteTemplate(id: string) {
  return api.delete<ApiResponse<any>>(`/templates/${id}`)
}
