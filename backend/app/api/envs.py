import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.env import Env, EnvSnapshot, AdjustmentHistory, TrainingMetric
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.env import (
    EnvCreate,
    EnvUpdate,
    EnvResponse,
    EnvAdjustRequest,
    EnvRollbackRequest,
    EnvSnapshotResponse,
    EnvBatchCreate,
    EnvImportRequest,
)
from app.schemas.env_config import EnvConfig
from app.core.deps import get_current_active_user
from app.services.config_parser import parse_json_config, parse_xml_config
from app.services.preview_generator import generate_scene_data
from app.tasks.env_tasks import generate_env_task, batch_generate_envs_task

router = APIRouter(prefix="/envs", tags=["envs"])


@router.get("", response_model=PaginatedResponse[EnvResponse])
async def list_envs(
    project_id: str | None = None,
    task_id: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(Env)
    count_stmt = select(func.count(Env.id))

    if project_id:
        stmt = stmt.where(Env.project_id == project_id)
        count_stmt = count_stmt.where(Env.project_id == project_id)
    if task_id:
        stmt = stmt.where(Env.task_id == task_id)
        count_stmt = count_stmt.where(Env.task_id == task_id)
    if status_filter:
        stmt = stmt.where(Env.status == status_filter)
        count_stmt = count_stmt.where(Env.status == status_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(Env.created_at.desc()).offset(offset).limit(page_size))
    envs = result.scalars().all()

    return PaginatedResponse(
        data=[EnvResponse.model_validate(e) for e in envs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ResponseModel[EnvResponse], status_code=201)
async def create_env(
    request: EnvCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    env = Env(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        task_id=request.task_id,
        name=request.name,
        config=request.config,
        template_id=request.template_id,
        status="draft",
        created_by=current_user.id,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    return ResponseModel(data=EnvResponse.model_validate(env))


@router.get("/{env_id}", response_model=ResponseModel[EnvResponse])
async def get_env(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    return ResponseModel(data=EnvResponse.model_validate(env))


@router.put("/{env_id}", response_model=ResponseModel[EnvResponse])
async def update_env(
    env_id: str,
    request: EnvUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    if request.name is not None:
        env.name = request.name
    if request.config is not None:
        env.config = request.config
    if request.status is not None:
        env.status = request.status

    await db.commit()
    await db.refresh(env)
    return ResponseModel(data=EnvResponse.model_validate(env))


@router.delete("/{env_id}", response_model=ResponseModel)
async def delete_env(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    await db.delete(env)
    await db.commit()
    return ResponseModel(message="Environment deleted successfully")


@router.post("/{env_id}/adjust", response_model=ResponseModel[EnvResponse])
async def adjust_env(
    env_id: str,
    request: EnvAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    old_config = dict(env.config) if env.config else {}

    snapshot_before = EnvSnapshot(
        id=str(uuid.uuid4()),
        env_id=env_id,
        config=old_config,
        trigger_type="manual_adjust",
        operator=current_user.id,
        reason=request.reason,
    )
    db.add(snapshot_before)
    await db.flush()

    new_config = dict(old_config)
    for key, value in request.config.items():
        if key in new_config and isinstance(new_config[key], dict) and isinstance(value, dict):
            new_config[key].update(value)
        else:
            new_config[key] = value

    env.config = new_config

    snapshot_after = EnvSnapshot(
        id=str(uuid.uuid4()),
        env_id=env_id,
        config=new_config,
        trigger_type="manual_adjust",
        operator=current_user.id,
        reason=request.reason,
    )
    db.add(snapshot_after)
    await db.flush()

    history = AdjustmentHistory(
        id=str(uuid.uuid4()),
        env_id=env_id,
        snapshot_before=snapshot_before.id,
        snapshot_after=snapshot_after.id,
        trigger_type="manual",
        operator=current_user.id,
        metric_change={"adjusted_keys": list(request.config.keys())},
    )
    db.add(history)

    await db.commit()
    await db.refresh(env)
    return ResponseModel(data=EnvResponse.model_validate(env))


@router.post("/{env_id}/rollback", response_model=ResponseModel[EnvResponse])
async def rollback_env(
    env_id: str,
    request: EnvRollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    snapshot_result = await db.execute(
        select(EnvSnapshot).where(EnvSnapshot.id == request.snapshot_id)
    )
    snapshot = snapshot_result.scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    env.config = snapshot.config
    env.status = "draft"

    rollback_snapshot = EnvSnapshot(
        id=str(uuid.uuid4()),
        env_id=env_id,
        config=snapshot.config,
        trigger_type="rollback",
        operator=current_user.id,
        reason=request.reason or f"Rolled back to snapshot {request.snapshot_id}",
    )
    db.add(rollback_snapshot)

    history = AdjustmentHistory(
        id=str(uuid.uuid4()),
        env_id=env_id,
        snapshot_before=None,
        snapshot_after=rollback_snapshot.id,
        trigger_type="rollback",
        operator=current_user.id,
        metric_change=None,
    )
    db.add(history)

    await db.commit()
    await db.refresh(env)
    return ResponseModel(data=EnvResponse.model_validate(env))


@router.get("/{env_id}/snapshots", response_model=PaginatedResponse[EnvSnapshotResponse])
async def list_snapshots(
    env_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(EnvSnapshot.id)).where(EnvSnapshot.env_id == env_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(EnvSnapshot)
        .where(EnvSnapshot.env_id == env_id)
        .order_by(EnvSnapshot.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    snapshots = result.scalars().all()

    return PaginatedResponse(
        data=[EnvSnapshotResponse.model_validate(s) for s in snapshots],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{env_id}/generate", response_model=ResponseModel)
async def generate_env(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    env.status = "generating"
    await db.commit()

    task_id = None
    try:
        task = generate_env_task.delay(env_id)
        task_id = task.id
    except Exception:
        pass

    return ResponseModel(
        message="Environment generation started",
        data={"task_id": task_id, "env_id": env_id},
    )


@router.post("/batch", response_model=ResponseModel)
async def batch_generate(
    request: EnvBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    env_ids = []
    for config in request.configs:
        env = Env(
            id=str(uuid.uuid4()),
            project_id=request.project_id,
            task_id=request.task_id,
            name=config.get("name", f"env_{uuid.uuid4().hex[:8]}"),
            config=config,
            status="draft",
            created_by=current_user.id,
        )
        db.add(env)
        await db.flush()
        env_ids.append(env.id)

    await db.commit()

    # Celery task (optional — skip if Redis not available)
    task_id = None
    try:
        task = batch_generate_envs_task.delay(env_ids)
        task_id = task.id
    except Exception:
        pass

    return ResponseModel(
        message="Batch environment generation started",
        data={"task_id": task_id, "env_ids": env_ids},
    )


@router.post("/import", response_model=ResponseModel[EnvResponse])
async def import_env(
    request: EnvImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        if request.file_type == "json":
            config = parse_json_config(request.file_content)
        elif request.file_type == "xml":
            config = parse_xml_config(request.file_content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {request.file_type}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    env = Env(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        task_id=request.task_id,
        name=request.name,
        config=config.model_dump(),
        status="draft",
        created_by=current_user.id,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)

    return ResponseModel(data=EnvResponse.model_validate(env))


@router.get("/{env_id}/export")
async def export_env(
    env_id: str,
    file_type: str = Query("json", enum=["json", "xml"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    if file_type == "json":
        content = json.dumps(env.config or {}, indent=2)
        media_type = "application/json"
        filename = f"env_{env_id}.json"
    else:
        content = _config_to_xml(env.config or {})
        media_type = "application/xml"
        filename = f"env_{env_id}.xml"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _config_to_xml(config: dict) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<environment>"]
    terrain = config.get("terrain", {})
    lines.append(f'  <terrain type="{terrain.get("type", "plains")}" '
                 f'elevation_min="{terrain.get("elevation_min", 0)}" '
                 f'elevation_max="{terrain.get("elevation_max", 3000)}" '
                 f'resolution="{terrain.get("resolution", 1.0)}" />')
    weather = config.get("weather", {})
    lines.append(f'  <weather wind_speed="{weather.get("wind_speed", 5)}" '
                 f'wind_direction="{weather.get("wind_direction", 0)}" '
                 f'visibility="{weather.get("visibility", 10000)}" />')
    lines.append("</environment>")
    return "\n".join(lines)


@router.get("/{env_id}/preview")
async def get_preview(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Env).where(Env.id == env_id))
    env = result.scalar_one_or_none()
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")

    config_data = env.config or {}
    try:
        config = EnvConfig(**config_data)
    except Exception:
        config = EnvConfig()

    scene_data = generate_scene_data(config)
    return ResponseModel(data=scene_data)


@router.get("/{env_id}/adjustment-history", response_model=PaginatedResponse)
async def get_adjustment_history(
    env_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(AdjustmentHistory.id)).where(AdjustmentHistory.env_id == env_id)
    )
    total = count_result.scalar()
    result = await db.execute(
        select(AdjustmentHistory)
        .where(AdjustmentHistory.env_id == env_id)
        .order_by(AdjustmentHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(data=[i.__dict__ for i in items], total=total, page=page, page_size=page_size)


@router.get("/{env_id}/history", response_model=PaginatedResponse)
async def get_env_history(
    env_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(AdjustmentHistory.id)).where(AdjustmentHistory.env_id == env_id)
    )
    total = count_result.scalar()
    result = await db.execute(
        select(AdjustmentHistory)
        .where(AdjustmentHistory.env_id == env_id)
        .order_by(AdjustmentHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(data=[{k: v for k, v in i.__dict__.items() if k != "env"} for i in items], total=total, page=page, page_size=page_size)


@router.get("/{env_id}/metrics", response_model=PaginatedResponse)
async def get_env_metrics(
    env_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(TrainingMetric.id)).where(TrainingMetric.env_id == env_id)
    )
    total = count_result.scalar()
    result = await db.execute(
        select(TrainingMetric)
        .where(TrainingMetric.env_id == env_id)
        .order_by(TrainingMetric.reported_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(data=[{k: v for k, v in i.__dict__.items() if k != "env"} for i in items], total=total, page=page, page_size=page_size)


@router.post("/generate", response_model=ResponseModel, status_code=201)
async def generate_env(
    request: EnvCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    env = Env(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        template_id=request.template_id,
        name=request.name,
        config=request.config.model_dump() if request.config else {},
        created_by=current_user.id,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return ResponseModel(data=EnvResponse.model_validate(env))
