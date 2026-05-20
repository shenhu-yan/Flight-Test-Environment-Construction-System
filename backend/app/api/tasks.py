import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_member, require_project_configurer
from app.schemas.project import TaskCreate, TaskUpdate

router = APIRouter()


@router.get("/{project_id}/tasks")
async def get_tasks(
    project_id: str,
    current_user: dict = Depends(require_project_member),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, project_id, name, description, created_by, created_at
            FROM tasks WHERE project_id = :project_id
            ORDER BY created_at DESC
            """
        ),
        {"project_id": project_id}
    )
    tasks = result.fetchall()
    return {
        "code": 0,
        "data": [
            {"id": t[0], "project_id": t[1], "name": t[2], "description": t[3], "created_by": t[4], "created_at": str(t[5]) if t[5] else None}
            for t in tasks
        ]
    }


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    task_data: TaskCreate,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO tasks (id, project_id, name, description, created_by, created_at)
            VALUES (:id, :project_id, :name, :description, :created_by, NOW())
            """
        ),
        {
            "id": task_id,
            "project_id": project_id,
            "name": task_data.name,
            "description": task_data.description,
            "created_by": current_user["id"],
        }
    )

    return {"code": 0, "data": {"id": task_id, "name": task_data.name}}


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, project_id, name, description, created_by, created_at FROM tasks WHERE id = :id"),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return {
        "code": 0,
        "data": {
            "id": task[0],
            "project_id": task[1],
            "name": task[2],
            "description": task[3],
            "created_by": task[4],
            "created_at": str(task[5]) if task[5] else None,
        }
    }


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM tasks WHERE id = :id"),
        {"id": task_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updates = []
    params = {"id": task_id}
    if task_data.name:
        updates.append("name = :name")
        params["name"] = task_data.name
    if task_data.description is not None:
        updates.append("description = :description")
        params["description"] = task_data.description

    if updates:
        await db.execute(
            text(f"UPDATE tasks SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id"),
            params
        )

    return {"code": 0, "message": "Task updated successfully"}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM tasks WHERE id = :id"),
        {"id": task_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": task_id})
    return {"code": 0, "message": "Task deleted successfully"}
