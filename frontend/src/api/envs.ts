import api from './index'
import type { ApiResponse, PaginatedResponse, FlightEnv, EnvConfig, EnvSnapshot, AdjustmentHistory, EnvEvaluation, SceneData } from '../types'

export function getEnvs(projectId: string, params?: { page?: number; page_size?: number; status?: string }) {
  return api.get<ApiResponse<PaginatedResponse<FlightEnv>>>(`/projects/${projectId}/envs`, { params })
}

export function getEnv(id: string) {
  return api.get<ApiResponse<FlightEnv>>(`/envs/${id}`)
}

export function createEnv(projectId: string, data: { name: string; config: EnvConfig; template_id?: string; task_id?: string }) {
  return api.post<ApiResponse<FlightEnv>>(`/projects/${projectId}/envs`, data)
}

export function deleteEnv(id: string) {
  return api.delete<ApiResponse<any>>(`/envs/${id}`)
}

export function adjustEnv(id: string, data: { adjustments: Partial<EnvConfig>; reason: string }) {
  return api.post<ApiResponse<FlightEnv>>(`/envs/${id}/adjust`, data)
}

export function rollbackEnv(id: string, snapshotId: string) {
  return api.post<ApiResponse<FlightEnv>>(`/envs/${id}/rollback`, { snapshot_id: snapshotId })
}

export function getSnapshots(envId: string) {
  return api.get<ApiResponse<EnvSnapshot[]>>(`/envs/${envId}/snapshots`)
}

export function getAdjustmentHistory(envId: string) {
  return api.get<ApiResponse<AdjustmentHistory[]>>(`/envs/${envId}/adjustment-history`)
}

export function exportEnv(id: string) {
  return api.get<Blob>(`/envs/${id}/export`, { responseType: 'blob' })
}

export function importEnv(projectId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post<ApiResponse<FlightEnv>>(`/projects/${projectId}/envs/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function batchGenerate(projectId: string, data: { count: number; config: EnvConfig }) {
  return api.post<ApiResponse<FlightEnv[]>>(`/projects/${projectId}/envs/batch`, data)
}

export function generateEnv(projectId: string, data: { name: string; config: EnvConfig; template_id?: string }) {
  return api.post<ApiResponse<FlightEnv>>(`/projects/${projectId}/envs/generate`, data)
}

export function getPreview(envId: string) {
  return api.get<ApiResponse<SceneData>>(`/envs/${envId}/preview`)
}

export function evaluateEnv(envId: string) {
  return api.post<ApiResponse<EnvEvaluation>>(`/envs/${envId}/evaluate`)
}

export function getEvaluations(envId: string) {
  return api.get<ApiResponse<EnvEvaluation[]>>(`/envs/${envId}/evaluations`)
}

export function getEnvHistory(envId: string) {
  return api.get<ApiResponse<AdjustmentHistory[]>>(`/envs/${envId}/history`)
}

export function updateEnv(id: string, data: Partial<FlightEnv>) {
  return api.put<ApiResponse<FlightEnv>>(`/envs/${id}`, data)
}
