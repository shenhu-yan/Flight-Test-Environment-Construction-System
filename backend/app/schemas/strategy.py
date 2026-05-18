from datetime import datetime

from pydantic import BaseModel


class StrategyRuleCreate(BaseModel):
    project_id: str | None = None
    name: str
    condition_config: dict
    action_config: dict
    priority: int = 0
    enabled: bool = True


class StrategyRuleUpdate(BaseModel):
    name: str | None = None
    condition_config: dict | None = None
    action_config: dict | None = None
    priority: int | None = None
    enabled: bool | None = None


class StrategyRuleResponse(BaseModel):
    id: str
    project_id: str | None = None
    name: str
    condition_config: dict
    action_config: dict
    priority: int
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
