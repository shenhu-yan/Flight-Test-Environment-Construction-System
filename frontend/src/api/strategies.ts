import api from './index'
import type { ApiResponse, StrategyRule } from '../types'

export function getStrategies(projectId?: string) {
  const params: any = {}
  if (projectId) params.project_id = projectId
  return api.get<ApiResponse<StrategyRule[]>>('/strategies', { params })
}

export function createStrategy(data: Partial<StrategyRule>) {
  return api.post<ApiResponse<StrategyRule>>('/strategies', data)
}

export function updateStrategy(id: string, data: Partial<StrategyRule>) {
  return api.put<ApiResponse<StrategyRule>>(`/strategies/${id}`, data)
}

export function deleteStrategy(id: string) {
  return api.delete<ApiResponse<any>>(`/strategies/${id}`)
}

export function toggleStrategy(id: string, enabled: boolean) {
  return api.patch<ApiResponse<StrategyRule>>(`/strategies/${id}`, { enabled })
}

export function getStrategy(id: string) {
  return api.get<ApiResponse<StrategyRule>>(`/strategies/${id}`)
}
