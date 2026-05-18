import api from './index'
import type { ApiResponse, ModelItem, ModelVersion } from '../types'

export function getModels(params?: { page?: number; page_size?: number; project_id?: string; type?: string; status?: string }) {
  return api.get<ApiResponse<ModelItem[]>>('/models', { params })
}

export function getModel(id: string) {
  return api.get<ApiResponse<ModelItem>>(`/models/${id}`)
}

export function uploadModel(data: { name: string; type: string; description?: string }, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', data.name)
  formData.append('type', data.type)
  if (data.description) formData.append('description', data.description)
  return api.post<ApiResponse<ModelItem>>('/models', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteModel(id: string) {
  return api.delete<ApiResponse<any>>(`/models/${id}`)
}

export function getModelVersions(modelId: string) {
  return api.get<ApiResponse<ModelVersion[]>>(`/models/${modelId}/versions`)
}

export function uploadModelVersion(modelId: string, file: File, metadata?: any) {
  const formData = new FormData()
  formData.append('file', file)
  if (metadata) formData.append('metadata', JSON.stringify(metadata))
  return api.post<ApiResponse<ModelVersion>>(`/models/${modelId}/versions`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function diffVersions(modelId: string, version1: string, version2: string) {
  return api.get<ApiResponse<any>>(`/models/${modelId}/diff`, { params: { version1, version2 } })
}

export function rollbackModel(modelId: string, version: string) {
  return api.post<ApiResponse<ModelItem>>(`/models/${modelId}/rollback`, { version })
}

export function downloadModelVersion(modelId: string, version: string) {
  return api.get<ApiResponse<string>>(`/models/${modelId}/download`, { params: { version } })
}
