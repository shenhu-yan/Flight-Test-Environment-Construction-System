import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_member, require_project_configurer
from app.schemas.project import ProjectCreate, ProjectUpdate, MemberAdd

router = APIRouter()


@router.get("")
async def get_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT p.id, p.name, p.description, p.created_by, p.created_at
            FROM projects p
            LEFT JOIN project_roles pr ON p.id = pr.project_id
            WHERE pr.user_id = :user_id OR p.created_by = :user_id
            ORDER BY p.created_at DESC
            """
        ),
        {"user_id": current_user["id"]}
    )
    projects = result.fetchall()
    return {
        "code": 0,
        "data": [
            {"id": p[0], "name": p[1], "description": p[2], "created_by": p[3], "created_at": str(p[4]) if p[4] else None}
            for p in projects
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO projects (id, name, description, created_by, created_at)
            VALUES (:id, :name, :description, :created_by, NOW())
            """
        ),
        {
            "id": project_id,
            "name": project_data.name,
            "description": project_data.description,
            "created_by": current_user["id"],
        }
    )

    await db.execute(
        text(
            """
            INSERT INTO project_roles (id, user_id, project_id, role)
            VALUES (:id, :user_id, :project_id, 'admin')
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "project_id": project_id,
        }
    )

    return {"code": 0, "data": {"id": project_id, "name": project_data.name}}


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(require_project_member),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, name, description, created_by, created_at FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    project = result.fetchone()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return {
        "code": 0,
        "data": {
            "id": project[0],
            "name": project[1],
            "description": project[2],
            "created_by": project[3],
            "created_at": str(project[4]) if project[4] else None,
        }
    }


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    updates = []
    params = {"id": project_id}
    if project_data.name:
        updates.append("name = :name")
        params["name"] = project_data.name
    if project_data.description is not None:
        updates.append("description = :description")
        params["description"] = project_data.description

    if updates:
        await db.execute(
            text(f"UPDATE projects SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id"),
            params
        )

    return {"code": 0, "message": "Project updated successfully"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # 获取项目下所有环境ID
    env_result = await db.execute(
        text("SELECT id FROM envs WHERE project_id = :project_id"),
        {"project_id": project_id}
    )
    env_ids = [row[0] for row in env_result.fetchall()]

    if env_ids:
        env_id_list = ", ".join([f"'{eid}'" for eid in env_ids])

        # 删除环境相关的子表数据
        await db.execute(text(f"DELETE FROM training_metrics WHERE env_id IN ({env_id_list})"))
        await db.execute(text(f"DELETE FROM env_evaluations WHERE env_id IN ({env_id_list})"))
        await db.execute(text(f"DELETE FROM adjustment_history WHERE env_id IN ({env_id_list})"))
        await db.execute(text(f"DELETE FROM env_snapshots WHERE env_id IN ({env_id_list})"))

    # 删除环境
    await db.execute(text("DELETE FROM envs WHERE project_id = :id"), {"id": project_id})

    # 获取项目下所有优化任务ID
    opt_result = await db.execute(
        text("SELECT id FROM optimization_tasks WHERE project_id = :project_id"),
        {"project_id": project_id}
    )
    opt_ids = [row[0] for row in opt_result.fetchall()]

    if opt_ids:
        opt_id_list = ", ".join([f"'{oid}'" for oid in opt_ids])
        await db.execute(text(f"DELETE FROM optimization_reports WHERE task_id IN ({opt_id_list})"))

    # 删除优化任务
    await db.execute(text("DELETE FROM optimization_tasks WHERE project_id = :id"), {"id": project_id})

    # 获取项目下所有模型ID
    model_result = await db.execute(
        text("SELECT id FROM models WHERE project_id = :project_id"),
        {"project_id": project_id}
    )
    model_ids = [row[0] for row in model_result.fetchall()]

    if model_ids:
        model_id_list = ", ".join([f"'{mid}'" for mid in model_ids])
        await db.execute(text(f"DELETE FROM model_versions WHERE model_id IN ({model_id_list})"))

    # 删除模型
    await db.execute(text("DELETE FROM models WHERE project_id = :id"), {"id": project_id})

    # 删除策略、任务、项目角色、项目
    await db.execute(text("DELETE FROM strategies WHERE project_id = :id"), {"id": project_id})
    await db.execute(text("DELETE FROM tasks WHERE project_id = :id"), {"id": project_id})
    await db.execute(text("DELETE FROM project_roles WHERE project_id = :id"), {"id": project_id})
    await db.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})

    await db.commit()
    return {"code": 0, "message": "Project deleted successfully"}


@router.get("/{project_id}/members")
async def get_members(
    project_id: str,
    current_user: dict = Depends(require_project_member),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT pr.id, pr.user_id, pr.role, u.username
            FROM project_roles pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.project_id = :project_id
            """
        ),
        {"project_id": project_id}
    )
    members = result.fetchall()
    return {
        "code": 0,
        "data": [
            {"id": m[0], "user_id": m[1], "role": m[2], "username": m[3]}
            for m in members
        ]
    }


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: str,
    member_data: MemberAdd,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        text("SELECT id FROM project_roles WHERE user_id = :user_id AND project_id = :project_id"),
        {"user_id": member_data.user_id, "project_id": project_id}
    )
    if existing.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member")

    await db.execute(
        text(
            """
            INSERT INTO project_roles (id, user_id, project_id, role)
            VALUES (:id, :user_id, :project_id, :role)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": member_data.user_id,
            "project_id": project_id,
            "role": member_data.role,
        }
    )
    await db.commit()

    return {"code": 0, "message": "Member added successfully"}


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: str,
    user_id: str,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        text("DELETE FROM project_roles WHERE user_id = :user_id AND project_id = :project_id"),
        {"user_id": user_id, "project_id": project_id}
    )
    await db.commit()
    return {"code": 0, "message": "Member removed successfully"}


@router.put("/{project_id}/members/{user_id}")
async def update_member_role(
    project_id: str,
    user_id: str,
    role_data: dict,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM project_roles WHERE user_id = :user_id AND project_id = :project_id"),
        {"user_id": user_id, "project_id": project_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    await db.execute(
        text("UPDATE project_roles SET role = :role WHERE user_id = :user_id AND project_id = :project_id"),
        {"role": role_data.get("role", "viewer"), "user_id": user_id, "project_id": project_id}
    )
    await db.commit()
    return {"code": 0, "message": "Member role updated"}
