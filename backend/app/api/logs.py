import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()


@router.get("/operations")
async def get_operation_logs(
    user_id: str = Query(None),
    action: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, user_id, action, resource_type, resource_id, detail, ip_address, created_at FROM operation_logs WHERE 1=1"
    params = {}

    if user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id
    if action:
        query += " AND action = :action"
        params["action"] = action
    if start_date:
        query += " AND created_at >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND created_at <= :end_date"
        params["end_date"] = end_date

    query += " ORDER BY created_at DESC"
    query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"

    result = await db.execute(text(query), params)
    logs = result.fetchall()

    count_query = "SELECT COUNT(*) FROM operation_logs WHERE 1=1"
    count_result = await db.execute(text(count_query), params)
    total = count_result.scalar()

    return {
        "code": 0,
        "data": {
            "items": [
                {
                    "id": l[0],
                    "user_id": l[1],
                    "action": l[2],
                    "resource_type": l[3],
                    "resource_id": l[4],
                    "detail": l[5],
                    "ip_address": l[6],
                    "created_at": str(l[7]) if l[7] else None,
                }
                for l in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    }


@router.get("/system")
async def get_system_logs(
    level: str = Query(None),
    module: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, level, module, message, detail, created_at FROM system_logs WHERE 1=1"
    params = {}

    if level:
        query += " AND level = :level"
        params["level"] = level
    if module:
        query += " AND module = :module"
        params["module"] = module
    if start_date:
        query += " AND created_at >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND created_at <= :end_date"
        params["end_date"] = end_date

    query += " ORDER BY created_at DESC"
    query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"

    result = await db.execute(text(query), params)
    logs = result.fetchall()

    count_query = "SELECT COUNT(*) FROM system_logs WHERE 1=1"
    count_result = await db.execute(text(count_query), params)
    total = count_result.scalar()

    return {
        "code": 0,
        "data": {
            "items": [
                {
                    "id": l[0],
                    "level": l[1],
                    "module": l[2],
                    "message": l[3],
                    "detail": l[4],
                    "created_at": str(l[5]) if l[5] else None,
                }
                for l in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    }


@router.get("/audit")
async def get_audit_logs(
    user_id: str = Query(None),
    resource_type: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, user_id, action, resource_type, resource_id, detail, ip_address, created_at FROM operation_logs WHERE 1=1"
    params = {}

    if user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id
    if resource_type:
        query += " AND resource_type = :resource_type"
        params["resource_type"] = resource_type
    if start_date:
        query += " AND created_at >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND created_at <= :end_date"
        params["end_date"] = end_date

    query += " ORDER BY created_at DESC LIMIT 100"

    result = await db.execute(text(query), params)
    logs = result.fetchall()

    return {
        "code": 0,
        "data": [
            {
                "id": l[0],
                "user_id": l[1],
                "action": l[2],
                "resource_type": l[3],
                "resource_id": l[4],
                "detail": l[5],
                "ip_address": l[6],
                "created_at": str(l[7]) if l[7] else None,
            }
            for l in logs
        ]
    }


async def log_operation(user_id: str, action: str, resource_type: str, resource_id: str, detail: dict, ip_address: str, db: AsyncSession):
    await db.execute(
        text(
            """
            INSERT INTO operation_logs (id, user_id, action, resource_type, resource_id, detail, ip_address, created_at)
            VALUES (:id, :user_id, :action, :resource_type, :resource_id, :detail, :ip_address, NOW())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": detail,
            "ip_address": ip_address,
        }
    )
    await db.commit()


async def log_system(level: str, module: str, message: str, detail: dict, db: AsyncSession):
    await db.execute(
        text(
            """
            INSERT INTO system_logs (id, level, module, message, detail, created_at)
            VALUES (:id, :level, :module, :message, :detail, NOW())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "level": level,
            "module": module,
            "message": message,
            "detail": detail,
        }
    )
    await db.commit()
