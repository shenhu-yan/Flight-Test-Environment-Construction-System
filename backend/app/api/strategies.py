import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_admin

router = APIRouter()


@router.get("")
async def get_strategies(
    project_id: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, name, condition, action, priority, enabled, project_id, created_at FROM strategies WHERE 1=1"
    params = {}

    if project_id:
        query += " AND (project_id = :project_id OR project_id IS NULL)"
        params["project_id"] = project_id

    query += " ORDER BY priority ASC"

    result = await db.execute(text(query), params)
    strategies = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": s[0],
                "name": s[1],
                "condition": json.loads(s[2]) if isinstance(s[2], str) else s[2],
                "action": json.loads(s[3]) if isinstance(s[3], str) else s[3],
                "priority": s[4],
                "enabled": s[5],
                "project_id": s[6],
                "created_at": str(s[7]) if s[7] else None,
            }
            for s in strategies
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: dict,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    strategy_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO strategies (id, name, condition, action, priority, enabled, project_id, created_at)
            VALUES (:id, :name, :condition, :action, :priority, :enabled, :project_id, NOW())
            """
        ),
        {
            "id": strategy_id,
            "name": strategy_data.get("name"),
            "condition": json.dumps(strategy_data.get("condition")),
            "action": json.dumps(strategy_data.get("action")),
            "priority": strategy_data.get("priority", 0),
            "enabled": strategy_data.get("enabled", True),
            "project_id": strategy_data.get("project_id"),
        }
    )

    return {"code": 0, "data": {"id": strategy_id, "name": strategy_data.get("name")}}


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    strategy_data: dict,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM strategies WHERE id = :id"),
        {"id": strategy_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    updates = []
    params = {"id": strategy_id}
    if "name" in strategy_data:
        updates.append("name = :name")
        params["name"] = strategy_data["name"]
    if "condition" in strategy_data:
        updates.append("condition = :condition")
        params["condition"] = json.dumps(strategy_data["condition"])
    if "action" in strategy_data:
        updates.append("action = :action")
        params["action"] = json.dumps(strategy_data["action"])
    if "priority" in strategy_data:
        updates.append("priority = :priority")
        params["priority"] = strategy_data["priority"]
    if "enabled" in strategy_data:
        updates.append("enabled = :enabled")
        params["enabled"] = strategy_data["enabled"]

    if updates:
        await db.execute(
            text(f"UPDATE strategies SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id"),
            params
        )

    return {"code": 0, "message": "Strategy updated successfully"}
