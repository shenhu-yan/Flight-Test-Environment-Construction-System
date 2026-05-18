import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.security import hash_password

logger = logging.getLogger(__name__)


async def seed_users(db: AsyncSession):
    result = await db.execute(select(User).where(User.username == "admin"))
    existing = result.scalar_one_or_none()
    if existing is not None:
        logger.info("Admin user already exists, skipping seed")
        return

    admin_user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        global_role="admin",
    )
    db.add(admin_user)
    await db.commit()
    logger.info("Admin user seeded successfully (username: admin, password: admin123)")
