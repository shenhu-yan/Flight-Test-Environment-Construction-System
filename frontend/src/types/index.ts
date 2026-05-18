export interface User { id: string; username: string; global_role: string; created_at: string }
export interface TokenResponse { access_token: string; token_type: string }
export interface Project { id: string; name: string; description: string; created_by: string; created_at: string; updated_at: string }
export interface Task { id: string; project_id: string; name: string; description: string; created_by: string; created_at: string; updated_at: string }
export interface Template { id: string; name: string; aircraft_type: string; difficulty: string; config: EnvConfig; is_builtin: boolean; created_by: string; created_at: string }
export interface FlightEnv { id: string; project_id: string; task_id: string | null; name: string; config: EnvConfig; template_id: string | null; status: string; storage_path: string; created_by: string; created_at: string }
export interface EnvConfig {
  terrain: { type: string; elevation_min: number; elevation_max: number; resolution: number }
  weather: { wind_speed: number; wind_direction: number; visibility: number }
  flight_dynamics: { aircraft_model: string; mass: number; wingspan: number }
  rewards: { reward_items: { name: string; coefficient: number }[]; penalty_items: { name: string; coefficient: number }[] }
  obstacles: { count: number; types: string[]; density: number }
  waypoints: { id: string; position: number[]; order: number }[]
}
export interface SceneData { terrain: any; obstacles: any[]; waypoints: any[]; wind: any; runway: any }
export interface ModelItem { id: string; project_id: string; name: string; type: string; status: string; description: string; current_version: string; created_by: string; created_at: string; updated_at: string }
export interface ModelVersion { id: string; model_id: string; version: string; storage_path: string; metadata: any; download_count: number; created_at: string }
export interface EnvSnapshot { id: string; env_id: string; config: any; trigger_type: string; reason: string; created_at: string }
export interface AdjustmentHistory { id: string; env_id: string; trigger_type: string; operator: string; created_at: string }
export interface EnvEvaluation { id: string; env_id: string; diversity_score: number; challenge_score: number; realism_score: number; effectiveness_score: number; total_score: number; weights: any; suggestions: any; evaluated_at: string }
export interface TrainingMetric { id: number; env_id: string; episode_reward: number; success_rate: number; convergence_speed: number; step: number; reported_at: string }
export interface OptimizationTask { id: string; project_id: string; param_space: any; weights: any; max_iterations: number; current_iteration: number; status: string; best_params: any; best_score: number; created_at: string }
export interface OptimizationReport { id: string; task_id: string; before_scores: any; after_scores: any; comparison_data: any; created_at: string }
export interface StrategyRule { id: string; project_id: string | null; name: string; condition_config: any; action_config: any; priority: number; enabled: boolean; created_at: string }
export interface Notification { id: string; user_id: string; type: string; title: string; content: string; is_read: boolean; created_at: string }
export interface ApiResponse<T = any> { code: number; message: string; data: T }
export interface PaginatedResponse<T = any> { code: number; message: string; data: T[]; total: number; page: number; page_size: number }
