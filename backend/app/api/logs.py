from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.log import OperationLog, SystemLog, Notification
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.deps import get_current_active_user
from pydantic import BaseModel

router = APIRouter(tags=["logs"])


class OperationLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    detail: dict | None = None
    ip_address: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class SystemLogResponse(BaseModel):
    id: str
    level: str
    module: str
    message: str
    detail: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    content: str
    is_read: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/logs/operations", response_model=PaginatedResponse[OperationLogResponse])
async def list_operation_logs(
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(OperationLog)
    count_stmt = select(func.count(OperationLog.id))

    if user_id:
        stmt = stmt.where(OperationLog.user_id == user_id)
        count_stmt = count_stmt.where(OperationLog.user_id == user_id)
    if action:
        stmt = stmt.where(OperationLog.action == action)
        count_stmt = count_stmt.where(OperationLog.action == action)
    if resource_type:
        stmt = stmt.where(OperationLog.resource_type == resource_type)
        count_stmt = count_stmt.where(OperationLog.resource_type == resource_type)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(OperationLog.created_at.desc()).offset(offset).limit(page_size))
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append(OperationLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            detail=log.detail,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat() if log.created_at else "",
        ))

    return PaginatedResponse(data=items, total=total, page=page, page_size=page_size)


@router.get("/logs/system", response_model=PaginatedResponse[SystemLogResponse])
async def list_system_logs(
    level: str | None = None,
    module: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(SystemLog)
    count_stmt = select(func.count(SystemLog.id))

    if level:
        stmt = stmt.where(SystemLog.level == level)
        count_stmt = count_stmt.where(SystemLog.level == level)
    if module:
        stmt = stmt.where(SystemLog.module == module)
        count_stmt = count_stmt.where(SystemLog.module == module)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(SystemLog.created_at.desc()).offset(offset).limit(page_size))
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append(SystemLogResponse(
            id=log.id,
            level=log.level,
            module=log.module,
            message=log.message,
            detail=log.detail,
            created_at=log.created_at.isoformat() if log.created_at else "",
        ))

    return PaginatedResponse(data=items, total=total, page=page, page_size=page_size)


@router.get("/notifications", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    is_read: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    count_stmt = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
        count_stmt = count_stmt.where(Notification.is_read == is_read)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    result = await db.execute(stmt.order_by(Notification.created_at.desc()).offset(offset).limit(page_size))
    notifications = result.scalars().all()

    items = []
    for n in notifications:
        items.append(NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            title=n.title,
            content=n.content,
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if n.created_at else "",
        ))

    return PaginatedResponse(data=items, total=total, page=page, page_size=page_size)


@router.put("/notifications/{notification_id}/read", response_model=ResponseModel)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    return ResponseModel(message="Notification marked as read")


@router.put("/notifications/read-all", response_model=ResponseModel)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return ResponseModel(message="All notifications marked as read")
