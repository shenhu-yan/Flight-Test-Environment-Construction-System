from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings

app = FastAPI(
    title="Flight Test Environment Construction System",
    description="基于强化学习的飞行试验环境构建系统 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"code": 0, "message": "ok"}


from app.api import auth, users, projects, tasks, templates, envs, models, optimization, strategies, ws, notifications, logs

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(templates.router, prefix="/api/templates", tags=["模板"])
app.include_router(envs.router, prefix="/api/envs", tags=["环境"])
app.include_router(models.router, prefix="/api/models", tags=["模型"])
app.include_router(optimization.router, prefix="/api", tags=["优化"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["策略"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(logs.router, prefix="/api/logs", tags=["日志"])
app.include_router(ws.router, tags=["WebSocket"])


@app.on_event("startup")
async def startup_event():
    from app.core.database import engine, Base
    from app.seed.users import seed_default_admin
    from app.seed.templates import seed_builtin_templates
    from app.seed.strategies import seed_default_strategies

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_default_admin()
    await seed_builtin_templates()
    await seed_default_strategies()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
