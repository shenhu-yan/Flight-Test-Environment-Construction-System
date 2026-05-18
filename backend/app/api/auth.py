from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.common import ResponseModel, TokenResponse
from app.schemas.user import LoginRequest
from app.services.security import (
    create_access_token,
    verify_password,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ResponseModel[TokenResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(data={"sub": user.id, "username": user.username, "role": user.global_role})

    return ResponseModel(
        code=0,
        message="Login successful",
        data=TokenResponse(access_token=access_token),
    )


@router.post("/logout", response_model=ResponseModel)
async def logout(current_user: User = Depends(get_current_user)):
    return ResponseModel(code=0, message="Logout successful", data=None)
