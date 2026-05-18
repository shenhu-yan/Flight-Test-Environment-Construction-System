import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, async_session_factory
from app.api import auth, users, projects, tasks, envs, models_api, templates, strategies, optimization, logs
from app.api import ws as ws_module
from app.seed.users import seed_users
from app.seed.templates import seed_templates
from app.seed.strategies import seed_strategies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FLTECT backend...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Seed data
    try:
        async with async_session_factory() as db:
            await seed_users(db)
            await seed_templates(db)
            await seed_strategies(db)
    except Exception as e:
        logger.warning(f"Seeding error (non-fatal): {e}")

    try:
        from minio import Minio
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region="us-east-1",  # 添加这行

        )
        if not minio_client.bucket_exists(settings.BUCKET_NAME):
            minio_client.make_bucket(settings.BUCKET_NAME)
            logger.info(f"Created MinIO bucket: {settings.BUCKET_NAME}")
        else:
            logger.info(f"MinIO bucket '{settings.BUCKET_NAME}' already exists")
    except Exception as e:
        logger.warning(f"Could not initialize MinIO: {e}")

    # Start APScheduler for continuous optimization
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler started successfully")
    except Exception as e:
        logger.warning(f"Could not start APScheduler: {e}")

    # Start WebSocket heartbeat checker background task
    heartbeat_task = asyncio.create_task(ws_module.heartbeat_checker())
    logger.info("WebSocket heartbeat checker started")

    logger.info("FLTECT backend started successfully")
    yield

    logger.info("Shutting down FLTECT backend...")

    # Cancel heartbeat checker
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass

    # Stop APScheduler
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass

    await engine.dispose()


app = FastAPI(
    title="FLTECT - Flight Test Environment Construction System",
    description="Reinforcement Learning Flight Test Environment Construction System API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(envs.router, prefix="/api")
app.include_router(models_api.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(optimization.router, prefix="/api")
app.include_router(logs.router, prefix="/api")

# WebSocket router (no /api prefix — WebSocket uses /ws/...)
app.include_router(ws_module.router)


@app.get("/")
async def root():
    return {"message": "FLTECT API", "version": "2.0.0"}


@app.get("/health")
async def health():
    from app.api.ws import manager
    return {
        "status": "healthy",
        "version": "2.0.0",
        "ws_stats": manager.stats,
    }
