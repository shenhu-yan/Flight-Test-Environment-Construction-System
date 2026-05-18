import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.security import hash_password
from app.core.deps import require_admin, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return PaginatedResponse(
        data=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return ResponseModel(data=UserResponse.model_validate(current_user))


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ResponseModel(data=UserResponse.model_validate(user))


@router.post("", response_model=ResponseModel[UserResponse], status_code=201)
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.username == request.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        password_hash=hash_password(request.password),
        global_role=request.global_role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return ResponseModel(data=UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
async def update_user(
    user_id: str,
    request: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.id != user_id and current_user.global_role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if request.username is not None:
        existing = await db.execute(
            select(User).where(User.username == request.username, User.id != user_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = request.username

    if request.password is not None:
        user.password_hash = hash_password(request.password)

    if request.global_role is not None:
        if current_user.global_role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can change roles")
        user.global_role = request.global_role

    await db.commit()
    await db.refresh(user)
    return ResponseModel(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return ResponseModel(message="User deleted successfully")
