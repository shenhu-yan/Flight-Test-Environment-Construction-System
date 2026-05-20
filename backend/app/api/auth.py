from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, username, password_hash, global_role FROM users WHERE username = :username"),
        {"username": request.username}
    )
    user = result.fetchone()

    if not user or not verify_password(request.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user[1], "role": user[3]})
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"code": 0, "message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"code": 0, "data": current_user}
