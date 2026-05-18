from datetime import datetime

from pydantic import BaseModel


class EnvCreate(BaseModel):
    project_id: str
    task_id: str | None = None
    name: str
    config: dict | None = None
    template_id: str | None = None


class EnvUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    status: str | None = None


class EnvResponse(BaseModel):
    id: str
    project_id: str
    task_id: str | None = None
    name: str
    config: dict | None = None
    template_id: str | None = None
    status: str
    storage_path: str | None = None
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnvAdjustRequest(BaseModel):
    config: dict
    reason: str | None = None


class EnvRollbackRequest(BaseModel):
    snapshot_id: str
    reason: str | None = None


class EnvSnapshotResponse(BaseModel):
    id: str
    env_id: str
    config: dict
    trigger_type: str
    operator: str | None = None
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnvBatchCreate(BaseModel):
    project_id: str
    task_id: str | None = None
    configs: list[dict]


class EnvImportRequest(BaseModel):
    project_id: str
    task_id: str | None = None
    name: str
    file_content: str
    file_type: str = "json"


class EnvEvaluationResponse(BaseModel):
    id: str
    env_id: str
    diversity_score: float
    challenge_score: float
    realism_score: float
    effectiveness_score: float
    total_score: float
    weights: dict | None = None
    suggestions: list | None = None
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class TrainingMetricResponse(BaseModel):
    id: int
    env_id: str
    task_id: str | None = None
    episode_reward: float
    success_rate: float
    convergence_speed: float
    step: int
    reported_at: datetime

    model_config = {"from_attributes": True}
