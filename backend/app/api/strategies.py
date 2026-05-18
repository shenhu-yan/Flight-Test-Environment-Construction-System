import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.env import StrategyRule
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.strategy import StrategyRuleCreate, StrategyRuleUpdate, StrategyRuleResponse
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=ResponseModel[list[StrategyRuleResponse]])
async def list_strategies(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(StrategyRule).order_by(StrategyRule.priority.desc())
    if project_id:
        stmt = stmt.where(
            (StrategyRule.project_id == project_id) | (StrategyRule.project_id.is_(None))
        )
    else:
        stmt = stmt.where(StrategyRule.project_id.is_(None))

    result = await db.execute(stmt)
    rules = result.scalars().all()

    return ResponseModel(
        data=[StrategyRuleResponse.model_validate(r) for r in rules]
    )


@router.post("", response_model=ResponseModel[StrategyRuleResponse], status_code=201)
async def create_strategy(
    request: StrategyRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rule = StrategyRule(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        name=request.name,
        condition_config=request.condition_config,
        action_config=request.action_config,
        priority=request.priority,
        enabled=request.enabled,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return ResponseModel(data=StrategyRuleResponse.model_validate(rule))


@router.get("/{rule_id}", response_model=ResponseModel[StrategyRuleResponse])
async def get_strategy(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(StrategyRule).where(StrategyRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Strategy rule not found")
    return ResponseModel(data=StrategyRuleResponse.model_validate(rule))


@router.put("/{rule_id}", response_model=ResponseModel[StrategyRuleResponse])
async def update_strategy(
    rule_id: str,
    request: StrategyRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(StrategyRule).where(StrategyRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Strategy rule not found")

    if request.name is not None:
        rule.name = request.name
    if request.condition_config is not None:
        rule.condition_config = request.condition_config
    if request.action_config is not None:
        rule.action_config = request.action_config
    if request.priority is not None:
        rule.priority = request.priority
    if request.enabled is not None:
        rule.enabled = request.enabled

    await db.commit()
    await db.refresh(rule)
    return ResponseModel(data=StrategyRuleResponse.model_validate(rule))


@router.delete("/{rule_id}", response_model=ResponseModel)
async def delete_strategy(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(StrategyRule).where(StrategyRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Strategy rule not found")

    await db.delete(rule)
    await db.commit()
    return ResponseModel(message="Strategy rule deleted successfully")
