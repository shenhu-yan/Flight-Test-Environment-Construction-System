from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        text("SELECT id, username, global_role FROM users WHERE username = :username"),
        {"username": username}
    )
    user = result.fetchone()
    if user is None:
        raise credentials_exception
    return {"id": user[0], "username": user[1], "global_role": user[2]}


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["global_role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_project_member(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["global_role"] == "admin":
        return current_user

    result = await db.execute(
        text("SELECT role FROM project_roles WHERE user_id = :user_id AND project_id = :project_id"),
        {"user_id": current_user["id"], "project_id": project_id}
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a project member"
        )
    return {**current_user, "project_role": role}


async def require_project_configurer(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["global_role"] == "admin":
        return current_user

    result = await db.execute(
        text("SELECT role FROM project_roles WHERE user_id = :user_id AND project_id = :project_id"),
        {"user_id": current_user["id"], "project_id": project_id}
    )
    role = result.scalar_one_or_none()
    if role is None or role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Configurer privileges required"
        )
    return {**current_user, "project_role": role}
