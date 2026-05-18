import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.user import User, ProjectRole
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    MemberAdd,
    MemberResponse,
)
from app.core.deps import get_current_active_user

router = APIRouter(prefix="/projects", tags=["projects"])


async def _check_project_access(project_id: str, user: User, db: AsyncSession):
    if user.global_role == "admin":
        return True
    stmt = select(ProjectRole).where(
        ProjectRole.user_id == user.id,
        ProjectRole.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count(Project.id)))
    total = count_result.scalar()

    if current_user.global_role == "admin":
        stmt = select(Project).order_by(Project.created_at.desc()).offset(offset).limit(page_size)
    else:
        stmt = (
            select(Project)
            .join(ProjectRole, ProjectRole.project_id == Project.id)
            .where(ProjectRole.user_id == current_user.id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

    result = await db.execute(stmt)
    projects = result.scalars().all()

    return PaginatedResponse(
        data=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.post("", response_model=ResponseModel[ProjectResponse], status_code=201)
async def create_project(
    request: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    project = Project(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        created_by=current_user.id,
    )
    db.add(project)
    await db.flush()

    admin_role = ProjectRole(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        project_id=project.id,
        role="admin",
    )
    db.add(admin_role)
    await db.commit()
    await db.refresh(project)

    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.put("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description

    await db.commit()
    await db.refresh(project)
    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.created_by != current_user.id and current_user.global_role != "admin":
        stmt = select(ProjectRole).where(
            ProjectRole.user_id == current_user.id,
            ProjectRole.project_id == project_id,
            ProjectRole.role == "admin",
        )
        role_result = await db.execute(stmt)
        if role_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail="Only project admin can delete")

    await db.delete(project)
    await db.commit()
    return ResponseModel(message="Project deleted successfully")


@router.get("/{project_id}/members", response_model=PaginatedResponse[MemberResponse])
async def list_members(
    project_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(ProjectRole.id)).where(ProjectRole.project_id == project_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(ProjectRole)
        .where(ProjectRole.project_id == project_id)
        .offset(offset)
        .limit(page_size)
    )
    members = result.scalars().all()

    return PaginatedResponse(
        data=[MemberResponse.model_validate(m) for m in members],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{project_id}/members", response_model=ResponseModel[MemberResponse], status_code=201)
async def add_member(
    project_id: str,
    request: MemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    result = await db.execute(select(User).where(User.id == request.user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(ProjectRole).where(
            ProjectRole.user_id == request.user_id,
            ProjectRole.project_id == project_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="User is already a member")

    member = ProjectRole(
        id=str(uuid.uuid4()),
        user_id=request.user_id,
        project_id=project_id,
        role=request.role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return ResponseModel(data=MemberResponse.model_validate(member))


@router.delete("/{project_id}/members/{member_id}", response_model=ResponseModel)
async def remove_member(
    project_id: str,
    member_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    result = await db.execute(
        select(ProjectRole).where(
            ProjectRole.id == member_id,
            ProjectRole.project_id == project_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
    return ResponseModel(message="Member removed successfully")
