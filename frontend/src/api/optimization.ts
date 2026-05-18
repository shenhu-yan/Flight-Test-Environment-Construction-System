import api from './index'
import type { ApiResponse, OptimizationTask, OptimizationReport, EnvEvaluation } from '../types'

export function evaluateEnv(envId: string) {
  return api.post<ApiResponse<EnvEvaluation>>(`/envs/${envId}/evaluate`)
}

export function getEvaluations(envId: string) {
  return api.get<ApiResponse<EnvEvaluation[]>>(`/envs/${envId}/evaluations`)
}

export function createOptimizationTask(projectId: string, data: { param_space: any; weights: any; max_iterations: number }) {
  return api.post<ApiResponse<OptimizationTask>>(`/projects/${projectId}/optimization/tasks`, data)
}

export function getOptimizationTasks(projectId: string) {
  return api.get<ApiResponse<OptimizationTask[]>>(`/projects/${projectId}/optimization/tasks`)
}

export function getOptimizationTask(taskId: string) {
  return api.get<ApiResponse<OptimizationTask>>(`/optimization/tasks/${taskId}`)
}

export function stopOptimizationTask(taskId: string) {
  return api.post<ApiResponse<OptimizationTask>>(`/optimization/tasks/${taskId}/stop`)
}

export function getOptimizationReport(taskId: string) {
  return api.get<ApiResponse<OptimizationReport>>(`/optimization/tasks/${taskId}/report`)
}

export function getOptimizationReports(projectId: string) {
  return api.get<ApiResponse<OptimizationReport[]>>(`/projects/${projectId}/optimization/reports`)
}
