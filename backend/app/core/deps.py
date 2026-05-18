from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, ProjectRole
from app.services.security import get_current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.global_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_project_member(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if current_user.global_role == "admin":
        return current_user

    stmt = select(ProjectRole).where(
        ProjectRole.user_id == current_user.id,
        ProjectRole.project_id == project_id,
    )
    result = await db.execute(stmt)
    project_role = result.scalar_one_or_none()
    if project_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )
    return current_user


async def require_project_manager(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if current_user.global_role == "admin":
        return current_user

    stmt = select(ProjectRole).where(
        ProjectRole.user_id == current_user.id,
        ProjectRole.project_id == project_id,
    )
    result = await db.execute(stmt)
    project_role = result.scalar_one_or_none()
    if project_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )
    if project_role.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin role required for this action",
        )
    return current_user


def get_optional_user() -> Optional[User]:
    return None
