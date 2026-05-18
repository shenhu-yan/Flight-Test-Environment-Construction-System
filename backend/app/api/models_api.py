import uuid
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import ModelRecord, ModelVersion
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelVersionResponse,
    ModelVersionCreate,
    ModelDiffRequest,
)
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=PaginatedResponse[ModelResponse])
async def list_models(
    project_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(ModelRecord)
    count_stmt = select(func.count(ModelRecord.id))

    if project_id:
        stmt = stmt.where(ModelRecord.project_id == project_id)
        count_stmt = count_stmt.where(ModelRecord.project_id == project_id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(ModelRecord.created_at.desc()).offset(offset).limit(page_size))
    models = result.scalars().all()

    return PaginatedResponse(
        data=[ModelResponse.model_validate(m) for m in models],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ResponseModel[ModelResponse], status_code=201)
async def create_model(
    request: ModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    model = ModelRecord(
        id=str(uuid.uuid4()),
        project_id=request.project_id,
        name=request.name,
        type=request.type,
        description=request.description,
        created_by=current_user.id,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return ResponseModel(data=ModelResponse.model_validate(model))


@router.get("/{model_id}", response_model=ResponseModel[ModelResponse])
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ModelRecord).where(ModelRecord.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return ResponseModel(data=ModelResponse.model_validate(model))


@router.put("/{model_id}", response_model=ResponseModel[ModelResponse])
async def update_model(
    model_id: str,
    request: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ModelRecord).where(ModelRecord.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if request.name is not None:
        model.name = request.name
    if request.type is not None:
        model.type = request.type
    if request.status is not None:
        model.status = request.status
    if request.description is not None:
        model.description = request.description

    await db.commit()
    await db.refresh(model)
    return ResponseModel(data=ModelResponse.model_validate(model))


@router.delete("/{model_id}", response_model=ResponseModel)
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ModelRecord).where(ModelRecord.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()
    return ResponseModel(message="Model deleted successfully")


@router.get("/{model_id}/versions", response_model=PaginatedResponse[ModelVersionResponse])
async def list_versions(
    model_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(ModelVersion.id)).where(ModelVersion.model_id == model_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.model_id == model_id)
        .order_by(ModelVersion.version.desc())
        .offset(offset)
        .limit(page_size)
    )
    versions = result.scalars().all()

    return PaginatedResponse(
        data=[ModelVersionResponse.model_validate(v) for v in versions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{model_id}/versions", response_model=ResponseModel[ModelVersionResponse], status_code=201)
async def create_version(
    model_id: str,
    request: ModelVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ModelRecord).where(ModelRecord.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    new_version = model.current_version + 1
    version = ModelVersion(
        id=str(uuid.uuid4()),
        model_id=model_id,
        version=new_version,
        storage_path=request.storage_path,
        metadata_=request.metadata,
    )
    db.add(version)

    model.current_version = new_version
    model.status = "published"
    await db.commit()
    await db.refresh(version)

    return ResponseModel(data=ModelVersionResponse(
        id=version.id,
        model_id=version.model_id,
        version=version.version,
        storage_path=version.storage_path,
        metadata=version.metadata_,
        download_count=version.download_count,
        created_at=version.created_at,
    ))


@router.get("/{model_id}/diff")
async def diff_versions(
    model_id: str,
    version_a: int,
    version_b: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result_a = await db.execute(
        select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.version == version_a,
        )
    )
    va = result_a.scalar_one_or_none()

    result_b = await db.execute(
        select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.version == version_b,
        )
    )
    vb = result_b.scalar_one_or_none()

    if va is None or vb is None:
        raise HTTPException(status_code=404, detail="Version not found")

    diff = {
        "version_a": {"version": va.version, "storage_path": va.storage_path, "metadata": va.metadata_},
        "version_b": {"version": vb.version, "storage_path": vb.storage_path, "metadata": vb.metadata_},
        "differences": [],
    }

    meta_a = va.metadata_ or {}
    meta_b = vb.metadata_ or {}
    all_keys = set(list(meta_a.keys()) + list(meta_b.keys()))
    for key in all_keys:
        if meta_a.get(key) != meta_b.get(key):
            diff["differences"].append({
                "field": key,
                "old": meta_a.get(key),
                "new": meta_b.get(key),
            })

    return ResponseModel(data=diff)


@router.post("/{model_id}/rollback", response_model=ResponseModel[ModelResponse])
async def rollback_model(
    model_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ModelRecord).where(ModelRecord.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    version_result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.version == version,
        )
    )
    ver = version_result.scalar_one_or_none()
    if ver is None:
        raise HTTPException(status_code=404, detail="Version not found")

    model.current_version = version
    model.status = "rolled_back"
    await db.commit()
    await db.refresh(model)

    return ResponseModel(data=ModelResponse.model_validate(model))


@router.get("/{model_id}/download")
async def download_version(
    model_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    version_result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.version == version,
        )
    )
    ver = version_result.scalar_one_or_none()
    if ver is None:
        raise HTTPException(status_code=404, detail="Version not found")

    ver.download_count += 1
    await db.commit()

    content = json.dumps({
        "model_id": model_id,
        "version": ver.version,
        "storage_path": ver.storage_path,
        "metadata": ver.metadata_,
    }, indent=2)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=model_{model_id}_v{version}.json"},
    )
