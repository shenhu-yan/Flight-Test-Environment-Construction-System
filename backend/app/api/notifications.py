import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()


@router.get("")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, type, title, content, read, created_at
            FROM notifications WHERE user_id = :user_id
            ORDER BY created_at DESC
            """
        ),
        {"user_id": current_user["id"]}
    )
    notifications = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": n[0],
                "type": n[1],
                "title": n[2],
                "content": n[3],
                "read": n[4],
                "created_at": str(n[5]) if n[5] else None,
            }
            for n in notifications
        ]
    }


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM notifications WHERE id = :id AND user_id = :user_id"),
        {"id": notification_id, "user_id": current_user["id"]}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    await db.execute(
        text("UPDATE notifications SET read = true WHERE id = :id"),
        {"id": notification_id}
    )

    return {"code": 0, "message": "Notification marked as read"}


async def create_notification(user_id: str, type: str, title: str, content: str, db: AsyncSession):
    await db.execute(
        text(
            """
            INSERT INTO notifications (id, user_id, type, title, content, read, created_at)
            VALUES (:id, :user_id, :type, :title, :content, false, NOW())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": type,
            "title": title,
            "content": content,
        }
    )
    await db.commit()
