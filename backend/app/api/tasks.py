import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.models.user import User, ProjectRole
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.core.deps import get_current_active_user

router = APIRouter(tags=["tasks"])


async def _check_task_project_access(project_id: str, user: User, db: AsyncSession):
    if user.global_role == "admin":
        return True
    stmt = select(ProjectRole).where(
        ProjectRole.user_id == user.id,
        ProjectRole.project_id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


@router.get("/projects/{project_id}/tasks", response_model=PaginatedResponse[TaskResponse])
async def list_project_tasks(
    project_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_task_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(Task.id)).where(Task.project_id == project_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    tasks = result.scalars().all()

    return PaginatedResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/projects/{project_id}/tasks", response_model=ResponseModel[TaskResponse], status_code=201)
async def create_task(
    project_id: str,
    request: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not await _check_task_project_access(project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    project_result = await db.execute(select(Project).where(Project.id == project_id))
    if project_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=request.name,
        description=request.description,
        created_by=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return ResponseModel(data=TaskResponse.model_validate(task))


@router.get("/tasks/{task_id}", response_model=ResponseModel[TaskResponse])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if not await _check_task_project_access(task.project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    return ResponseModel(data=TaskResponse.model_validate(task))


@router.put("/tasks/{task_id}", response_model=ResponseModel[TaskResponse])
async def update_task(
    task_id: str,
    request: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if not await _check_task_project_access(task.project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    if request.name is not None:
        task.name = request.name
    if request.description is not None:
        task.description = request.description

    await db.commit()
    await db.refresh(task)
    return ResponseModel(data=TaskResponse.model_validate(task))


@router.delete("/tasks/{task_id}", response_model=ResponseModel)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if not await _check_task_project_access(task.project_id, current_user, db):
        raise HTTPException(status_code=403, detail="Not a member of this project")

    await db.delete(task)
    await db.commit()
    return ResponseModel(message="Task deleted successfully")
