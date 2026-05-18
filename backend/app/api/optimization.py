import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.env import Env
from app.models.optimization import OptimizationTask, OptimizationReport
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.env import EnvEvaluationResponse
from app.schemas.optimization import (
    OptimizationTaskCreate,
    OptimizationTaskResponse,
    OptimizationReportResponse,
)
from app.core.deps import get_current_active_user
from app.tasks.optimization_tasks import evaluate_env_task, run_optimization_task
from sqlalchemy import func

router = APIRouter(tags=["optimization"])


@router.post("/envs/{env_id}/evaluate", response_model=ResponseModel)
async def evaluate_env(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    task = evaluate_env_task.delay(env_id)
    return ResponseModel(
        message="Evaluation started",
        data={"task_id": task.id, "env_id": env_id},
    )


@router.get("/envs/{env_id}/evaluations", response_model=PaginatedResponse[EnvEvaluationResponse])
async def list_evaluations(
    env_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.models.env import EnvEvaluation

    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(EnvEvaluation.id)).where(EnvEvaluation.env_id == env_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(EnvEvaluation)
        .where(EnvEvaluation.env_id == env_id)
        .order_by(EnvEvaluation.evaluated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    evaluations = result.scalars().all()

    return PaginatedResponse(
        data=[EnvEvaluationResponse.model_validate(e) for e in evaluations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/optimization-tasks", response_model=ResponseModel[OptimizationTaskResponse], status_code=201)
async def create_optimization_task(
    request: OptimizationTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    opt_task = OptimizationTask(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        param_space=request.param_space,
        weights=request.weights,
        max_iterations=request.max_iterations,
        status="pending",
    )
    db.add(opt_task)
    await db.commit()
    await db.refresh(opt_task)

    return ResponseModel(data=OptimizationTaskResponse.model_validate(opt_task))


@router.get("/optimization-tasks", response_model=PaginatedResponse[OptimizationTaskResponse])
async def list_optimization_tasks(
    project_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(OptimizationTask)
    count_stmt = select(func.count(OptimizationTask.id))

    if project_id:
        stmt = stmt.where(OptimizationTask.project_id == project_id)
        count_stmt = count_stmt.where(OptimizationTask.project_id == project_id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(OptimizationTask.created_at.desc()).offset(offset).limit(page_size))
    tasks = result.scalars().all()

    return PaginatedResponse(
        data=[OptimizationTaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/optimization-tasks/{task_id}", response_model=ResponseModel[OptimizationTaskResponse])
async def get_optimization_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(OptimizationTask).where(OptimizationTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Optimization task not found")
    return ResponseModel(data=OptimizationTaskResponse.model_validate(task))


@router.post("/optimization-tasks/{task_id}/start", response_model=ResponseModel)
async def start_optimization(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(OptimizationTask).where(OptimizationTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Optimization task not found")

    if task.status not in ("pending", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot start task in status '{task.status}'")

    celery_task = run_optimization_task.delay(task_id)
    return ResponseModel(
        message="Optimization started",
        data={"task_id": task_id, "celery_task_id": celery_task.id},
    )


@router.delete("/optimization-tasks/{task_id}", response_model=ResponseModel)
async def delete_optimization_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(OptimizationTask).where(OptimizationTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Optimization task not found")

    await db.delete(task)
    await db.commit()
    return ResponseModel(message="Optimization task deleted successfully")


@router.get("/optimization-reports/{report_id}", response_model=ResponseModel[OptimizationReportResponse])
async def get_optimization_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(OptimizationReport).where(OptimizationReport.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Optimization report not found")
    return ResponseModel(data=OptimizationReportResponse.model_validate(report))
