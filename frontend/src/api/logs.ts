import api from './index'
import type { ApiResponse, PaginatedResponse, Notification, TrainingMetric } from '../types'

export function getOperationLogs(params?: { page?: number; page_size?: number; action?: string }) {
  return api.get<ApiResponse<PaginatedResponse<any>>>('/logs/operations', { params })
}

export function getSystemLogs(params?: { page?: number; page_size?: number; level?: string }) {
  return api.get<ApiResponse<PaginatedResponse<any>>>('/logs/system', { params })
}

export function getNotifications(params?: { page?: number; page_size?: number; is_read?: boolean }) {
  return api.get<ApiResponse<PaginatedResponse<Notification>>>('/notifications', { params })
}

export function markNotificationRead(id: string) {
  return api.put<ApiResponse<Notification>>(`/notifications/${id}/read`)
}

export function markAllNotificationsRead() {
  return api.put<ApiResponse<any>>('/notifications/read-all')
}

export function getTrainingMetrics(envId: string, params?: { page?: number; page_size?: number }) {
  return api.get<ApiResponse<PaginatedResponse<TrainingMetric>>>(`/envs/${envId}/metrics`, { params })
}
