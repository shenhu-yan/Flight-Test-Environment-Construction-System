import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.schemas.template import TemplateCreate, TemplateUpdate

router = APIRouter()


@router.get("")
async def get_templates(
    aircraft_type: str = Query(None),
    difficulty: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, name, aircraft_type, difficulty, config, is_builtin, created_by, created_at FROM templates WHERE 1=1"
    params = {}

    if aircraft_type:
        query += " AND aircraft_type = :aircraft_type"
        params["aircraft_type"] = aircraft_type
    if difficulty:
        query += " AND difficulty = :difficulty"
        params["difficulty"] = difficulty

    query += " ORDER BY is_builtin DESC, created_at DESC"

    result = await db.execute(text(query), params)
    templates = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": t[0],
                "name": t[1],
                "aircraft_type": t[2],
                "difficulty": t[3],
                "config": json.loads(t[4]) if isinstance(t[4], str) else t[4],
                "is_builtin": t[5],
                "created_by": t[6],
                "created_at": str(t[7]) if t[7] else None,
            }
            for t in templates
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    template_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO templates (id, name, aircraft_type, difficulty, config, is_builtin, created_by, created_at)
            VALUES (:id, :name, :aircraft_type, :difficulty, :config, false, :created_by, NOW())
            """
        ),
        {
            "id": template_id,
            "name": template_data.name,
            "aircraft_type": template_data.aircraft_type,
            "difficulty": template_data.difficulty,
            "config": json.dumps(template_data.config),
            "created_by": current_user["id"],
        }
    )

    return {"code": 0, "data": {"id": template_id, "name": template_data.name}}


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, is_builtin FROM templates WHERE id = :id"),
        {"id": template_id}
    )
    template = result.fetchone()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    if template[1] and current_user["global_role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify builtin template")

    updates = []
    params = {"id": template_id}
    if template_data.name:
        updates.append("name = :name")
        params["name"] = template_data.name
    if template_data.aircraft_type:
        updates.append("aircraft_type = :aircraft_type")
        params["aircraft_type"] = template_data.aircraft_type
    if template_data.difficulty:
        updates.append("difficulty = :difficulty")
        params["difficulty"] = template_data.difficulty
    if template_data.config:
        updates.append("config = :config")
        params["config"] = json.dumps(template_data.config)

    if updates:
        await db.execute(
            text(f"UPDATE templates SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id"),
            params
        )

    return {"code": 0, "message": "Template updated successfully"}


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, is_builtin FROM templates WHERE id = :id"),
        {"id": template_id}
    )
    template = result.fetchone()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    if template[1] and current_user["global_role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete builtin template")

    await db.execute(text("DELETE FROM templates WHERE id = :id"), {"id": template_id})
    return {"code": 0, "message": "Template deleted successfully"}
