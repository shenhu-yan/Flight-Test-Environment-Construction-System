import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.template import Template
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=PaginatedResponse[TemplateResponse])
async def list_templates(
    aircraft_type: str | None = None,
    difficulty: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(Template)
    count_stmt = select(func.count(Template.id))

    if aircraft_type:
        stmt = stmt.where(Template.aircraft_type == aircraft_type)
        count_stmt = count_stmt.where(Template.aircraft_type == aircraft_type)
    if difficulty:
        stmt = stmt.where(Template.difficulty == difficulty)
        count_stmt = count_stmt.where(Template.difficulty == difficulty)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(Template.created_at.desc()).offset(offset).limit(page_size))
    templates = result.scalars().all()

    return PaginatedResponse(
        data=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ResponseModel[TemplateResponse], status_code=201)
async def create_template(
    request: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    template = Template(
        id=str(uuid.uuid4()),
        name=request.name,
        aircraft_type=request.aircraft_type,
        difficulty=request.difficulty,
        config=request.config,
        is_builtin=False,
        created_by=current_user.id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return ResponseModel(data=TemplateResponse.model_validate(template))


@router.get("/{template_id}", response_model=ResponseModel[TemplateResponse])
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResponseModel(data=TemplateResponse.model_validate(template))


@router.put("/{template_id}", response_model=ResponseModel[TemplateResponse])
async def update_template(
    template_id: str,
    request: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_builtin and current_user.global_role != "admin":
        raise HTTPException(status_code=403, detail="Cannot modify builtin templates")

    if request.name is not None:
        template.name = request.name
    if request.aircraft_type is not None:
        template.aircraft_type = request.aircraft_type
    if request.difficulty is not None:
        template.difficulty = request.difficulty
    if request.config is not None:
        template.config = request.config

    await db.commit()
    await db.refresh(template)
    return ResponseModel(data=TemplateResponse.model_validate(template))


@router.delete("/{template_id}", response_model=ResponseModel)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete builtin templates")

    await db.delete(template)
    await db.commit()
    return ResponseModel(message="Template deleted successfully")
