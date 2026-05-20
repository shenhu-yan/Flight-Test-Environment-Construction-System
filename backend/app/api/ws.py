import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session
from app.services.ws_manager import manager
from app.services.strategy_engine import strategy_engine

router = APIRouter()


async def verify_ws_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except JWTError:
        return None


async def save_metric(env_id: str, task_id: str, metrics: dict):
    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO training_metrics (env_id, task_id, episode_reward, success_rate, convergence_speed, step, reported_at)
                VALUES (:env_id, :task_id, :episode_reward, :success_rate, :convergence_speed, :step, NOW())
                """
            ),
            {
                "env_id": env_id,
                "task_id": task_id,
                "episode_reward": metrics.get("episode_reward"),
                "success_rate": metrics.get("success_rate"),
                "convergence_speed": metrics.get("convergence_speed"),
                "step": metrics.get("step"),
            }
        )
        await session.commit()


@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    project_id = None
    env_id = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "metric_report":
                project_id = message.get("project_id")
                env_id = message.get("env_id")
                task_id = message.get("task_id")
                metrics = message.get("metrics", {})

                key = f"{project_id}:{env_id}"
                await manager.register_metrics(key, websocket)

                await save_metric(env_id, task_id, metrics)

                await manager.broadcast_metrics(project_id, {
                    "env_id": env_id,
                    "metrics": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })

                await strategy_engine.process_metric(project_id, env_id, metrics)

            elif message.get("type") == "heartbeat":
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

    except WebSocketDisconnect:
        if project_id and env_id:
            key = f"{project_id}:{env_id}"
            await manager.unregister_metrics(key)


@router.websocket("/ws/adjustment")
async def adjustment_websocket(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    project_id = None
    env_id = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "register":
                project_id = message.get("project_id")
                env_id = message.get("env_id")
                key = f"{project_id}:{env_id}"
                await manager.register_adjustment(key, websocket)

            elif message.get("type") == "heartbeat":
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

    except WebSocketDisconnect:
        if project_id and env_id:
            key = f"{project_id}:{env_id}"
            await manager.unregister_adjustment(key)


@router.websocket("/ws/frontend")
async def frontend_websocket(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    project_id = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                project_id = message.get("project_id")
                await manager.register_frontend(project_id, websocket)
                await websocket.send_text(json.dumps({"type": "subscribed", "project_id": project_id}))

            elif message.get("type") == "heartbeat":
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

    except WebSocketDisconnect:
        if project_id:
            await manager.unregister_frontend(project_id, websocket)
