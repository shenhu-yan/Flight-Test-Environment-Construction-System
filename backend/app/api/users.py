from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, get_password_hash
from app.schemas.auth import UserCreate, UserUpdate, UserOut

router = APIRouter()


@router.get("")
async def get_users(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, username, global_role, created_at FROM users ORDER BY created_at DESC")
    )
    users = result.fetchall()
    return {
        "code": 0,
        "data": [
            {"id": u[0], "username": u[1], "global_role": u[2], "created_at": str(u[3]) if u[3] else None}
            for u in users
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_data.username}
    )
    if existing.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    import uuid
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)

    await db.execute(
        text(
            """
            INSERT INTO users (id, username, password_hash, global_role, created_at)
            VALUES (:id, :username, :password_hash, :global_role, NOW())
            """
        ),
        {
            "id": user_id,
            "username": user_data.username,
            "password_hash": hashed_password,
            "global_role": user_data.global_role,
        }
    )

    await db.commit()
    return {"code": 0, "data": {"id": user_id, "username": user_data.username, "global_role": user_data.global_role}}


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM users WHERE id = :id"),
        {"id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = []
    params = {"id": user_id}
    if user_data.username:
        updates.append("username = :username")
        params["username"] = user_data.username
    if user_data.global_role:
        updates.append("global_role = :global_role")
        params["global_role"] = user_data.global_role

    if updates:
        await db.execute(
            text(f"UPDATE users SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id"),
            params
        )
    await db.commit()

    return {"code": 0, "message": "User updated successfully"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    password_data: dict,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM users WHERE id = :id"),
        {"id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    hashed_password = get_password_hash(password_data.get("password", ""))
    await db.execute(
        text("UPDATE users SET password_hash = :password_hash, updated_at = NOW() WHERE id = :id"),
        {"password_hash": hashed_password, "id": user_id}
    )
    await db.commit()
    return {"code": 0, "message": "Password reset successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM users WHERE id = :id"),
        {"id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    await db.commit()
    return {"code": 0, "message": "User deleted successfully"}
