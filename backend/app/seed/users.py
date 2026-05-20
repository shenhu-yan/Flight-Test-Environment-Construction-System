from sqlalchemy import text
from app.core.database import async_session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_default_admin():
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id FROM users WHERE username = 'admin'")
        )
        if result.fetchone() is None:
            hashed_password = pwd_context.hash("admin123")
            await session.execute(
                text(
                    """
                    INSERT INTO users (id, username, password_hash, global_role, created_at)
                    VALUES ('00000000-0000-0000-0000-000000000001', 'admin', :password_hash, 'admin', NOW())
                    """
                ),
                {"password_hash": hashed_password},
            )
            await session.commit()
