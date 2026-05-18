from datetime import datetime

from pydantic import BaseModel


class OptimizationTaskCreate(BaseModel):
    project_id: str
    param_space: dict
    weights: dict
    max_iterations: int = 100


class OptimizationTaskResponse(BaseModel):
    id: str
    project_id: str
    param_space: dict
    weights: dict
    max_iterations: int
    current_iteration: int
    status: str
    params: dict | None = None
    best_score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizationReportResponse(BaseModel):
    id: str
    task_id: str
    before_scores: dict
    after_scores: dict
    comparison_data: dict
    created_at: datetime

    model_config = {"from_attributes": True}
