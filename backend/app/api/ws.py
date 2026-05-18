"""
WebSocket endpoints for the flight test system.
Three channels: metrics, adjustment, frontend.
"""
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.env import TrainingMetric, EnvSnapshot, AdjustmentHistory, Env
from app.services.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Manages WebSocket connections across three channels."""

    def __init__(self):
        self.metrics_connections: dict[str, WebSocket] = {}  # key: project_id:env_id
        self.adjustment_connections: dict[str, WebSocket] = {}  # key: project_id:env_id
        self.frontend_connections: dict[str, list[WebSocket]] = {}  # project_id -> [ws]
        self.last_heartbeat: dict[WebSocket, float] = {}

    async def connect_metrics(self, project_id: str, env_id: str, ws: WebSocket):
        await ws.accept()
        key = f"{project_id}:{env_id}"
        # Close previous connection if exists
        old = self.metrics_connections.pop(key, None)
        if old:
            self.last_heartbeat.pop(old, None)
            try:
                await old.close(code=4001, reason="replaced by new connection")
            except Exception:
                pass
        self.metrics_connections[key] = ws
        self.last_heartbeat[ws] = time.time()
        logger.info(f"Metrics WS connected: {key}")

    async def connect_adjustment(self, project_id: str, env_id: str, ws: WebSocket):
        await ws.accept()
        key = f"{project_id}:{env_id}"
        old = self.adjustment_connections.pop(key, None)
        if old:
            self.last_heartbeat.pop(old, None)
            try:
                await old.close(code=4001, reason="replaced by new connection")
            except Exception:
                pass
        self.adjustment_connections[key] = ws
        self.last_heartbeat[ws] = time.time()
        logger.info(f"Adjustment WS connected: {key}")

    async def connect_frontend(self, project_id: str, ws: WebSocket):
        await ws.accept()
        if project_id not in self.frontend_connections:
            self.frontend_connections[project_id] = []
        self.frontend_connections[project_id].append(ws)
        self.last_heartbeat[ws] = time.time()
        logger.info(f"Frontend WS connected for project: {project_id}")

    def disconnect(self, ws: WebSocket):
        self.last_heartbeat.pop(ws, None)
        for key in list(self.metrics_connections.keys()):
            if self.metrics_connections[key] is ws:
                del self.metrics_connections[key]
                logger.debug(f"Metrics WS disconnected: {key}")
        for key in list(self.adjustment_connections.keys()):
            if self.adjustment_connections[key] is ws:
                del self.adjustment_connections[key]
                logger.debug(f"Adjustment WS disconnected: {key}")
        for pid in list(self.frontend_connections.keys()):
            if ws in self.frontend_connections[pid]:
                self.frontend_connections[pid].remove(ws)
                logger.debug(f"Frontend WS disconnected: {pid}")
        # Cleanup empty lists
        for pid in list(self.frontend_connections.keys()):
            if not self.frontend_connections[pid]:
                del self.frontend_connections[pid]

    async def broadcast_metrics(self, project_id: str, env_id: str, data: dict):
        """Broadcast metric data to all frontend connections for a project."""
        if project_id not in self.frontend_connections:
            return
        for ws in self.frontend_connections[project_id][:]:
            try:
                await ws.send_json({
                    "type": "metric_broadcast",
                    "env_id": env_id,
                    "data": data,
                })
            except Exception:
                self.frontend_connections[project_id].remove(ws)

    async def send_adjustment(self, project_id: str, env_id: str, instruction: dict):
        """Send an adjustment instruction to the local training process."""
        key = f"{project_id}:{env_id}"
        ws = self.adjustment_connections.get(key)
        if ws:
            try:
                await ws.send_json({
                    "type": "adjust_instruction",
                    **instruction,
                })
                logger.info(f"Adjustment instruction sent: {key}")
            except Exception:
                self.disconnect(ws)
        else:
            logger.warning(f"No adjustment connection for {key}")

    async def broadcast_notification(self, project_id: str, notification: dict):
        """Broadcast a notification to all frontend connections for a project."""
        if project_id not in self.frontend_connections:
            return
        for ws in self.frontend_connections[project_id][:]:
            try:
                await ws.send_json({
                    "type": "notification",
                    **notification,
                })
            except Exception:
                self.frontend_connections[project_id].remove(ws)

    def check_heartbeats(self, timeout: int = 60):
        """Return list of stale connections that should be disconnected."""
        now = time.time()
        stale = [ws for ws, t in self.last_heartbeat.items() if now - t > timeout]
        return stale

    def update_heartbeat(self, ws: WebSocket):
        """Update the heartbeat timestamp for a connection."""
        self.last_heartbeat[ws] = time.time()

    @property
    def stats(self) -> dict:
        return {
            "metrics_connections": len(self.metrics_connections),
            "adjustment_connections": len(self.adjustment_connections),
            "frontend_connections": sum(
                len(v) for v in self.frontend_connections.values()
            ),
            "total_tracked": len(self.last_heartbeat),
        }


# Global singleton
manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Background heartbeat checker
# ---------------------------------------------------------------------------
async def heartbeat_checker():
    """Background task that checks and disconnects stale connections every 30s."""
    while True:
        await asyncio.sleep(30)
        stale = manager.check_heartbeats(timeout=60)
        for ws in stale:
            logger.info("Disconnecting stale WebSocket connection")
            try:
                await ws.close(code=4002, reason="heartbeat timeout")
            except Exception:
                pass
            manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Helper: validate JWT from query param and return payload
# ---------------------------------------------------------------------------
def _validate_ws_token(token: str) -> dict:
    """Validate a JWT token for WebSocket auth. Returns payload dict."""
    from fastapi import HTTPException
    return decode_access_token(token)


# ---------------------------------------------------------------------------
# WebSocket 1: /ws/metrics — local training process reports metrics
# ---------------------------------------------------------------------------
@router.websocket("/ws/metrics")
async def ws_metrics(
    websocket: WebSocket,
    token: str = Query(...),
    project_id: str = Query(...),
    env_id: str = Query(...),
):
    """
    Local training processes connect here to report training metrics.
    
    Expected messages (JSON):
      - type: "metric_report"
        data: { episode_reward, success_rate, convergence_speed, step, ... }
      - type: "heartbeat"
    """
    # Authenticate
    try:
        payload = _validate_ws_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4003, reason="authentication failed")
        return

    await manager.connect_metrics(project_id, env_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "heartbeat":
                manager.update_heartbeat(websocket)
                await websocket.send_json({"type": "heartbeat_ack"})
                continue

            if msg_type == "metric_report":
                data = msg.get("data", {})
                manager.update_heartbeat(websocket)

                # Persist to database
                try:
                    async with async_session_factory() as db:
                        metric = TrainingMetric(
                            env_id=env_id,
                            episode_reward=data.get("episode_reward", 0.0),
                            success_rate=data.get("success_rate", 0.0),
                            convergence_speed=data.get("convergence_speed", 0.0),
                            step=data.get("step", 0),
                        )
                        db.add(metric)
                        await db.commit()
                except Exception as e:
                    logger.error(f"Failed to save metric: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "detail": f"Failed to save metric: {str(e)}",
                    })
                    continue

                # Push to Redis Stream for real-time consumers
                try:
                    import redis.asyncio as aioredis
                    redis_client = aioredis.from_url(settings.REDIS_URL)
                    stream_key = f"metrics:{project_id}:{env_id}"
                    await redis_client.xadd(
                        stream_key,
                        {
                            "episode_reward": str(data.get("episode_reward", 0.0)),
                            "success_rate": str(data.get("success_rate", 0.0)),
                            "convergence_speed": str(data.get("convergence_speed", 0.0)),
                            "step": str(data.get("step", 0)),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        maxlen=1000,
                    )
                    await redis_client.aclose()
                except Exception as e:
                    logger.warning(f"Redis push failed (non-critical): {e}")

                # Broadcast to frontend connections
                broadcast_data = {
                    "episode_reward": data.get("episode_reward", 0.0),
                    "success_rate": data.get("success_rate", 0.0),
                    "convergence_speed": data.get("convergence_speed", 0.0),
                    "step": data.get("step", 0),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await manager.broadcast_metrics(project_id, env_id, broadcast_data)

                # Acknowledge receipt
                await websocket.send_json({
                    "type": "metric_ack",
                    "step": data.get("step", 0),
                })

                # Run strategy evaluation in background
                try:
                    from app.services.strategy_engine import StrategyEngine
                    async with async_session_factory() as db:
                        engine = StrategyEngine(db)
                        adjustments = await engine.evaluate_metrics(env_id, broadcast_data)
                        if adjustments:
                            for adj in adjustments:
                                await manager.send_adjustment(project_id, env_id, adj)
                except Exception as e:
                    logger.error(f"Strategy evaluation failed: {e}")

            else:
                await websocket.send_json({
                    "type": "error",
                    "detail": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        logger.info(f"Metrics WS disconnected normally: {project_id}:{env_id}")
    except Exception as e:
        logger.error(f"Metrics WS error: {e}")
    finally:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# WebSocket 2: /ws/adjustment — local training process receives adjustments
# ---------------------------------------------------------------------------
@router.websocket("/ws/adjustment")
async def ws_adjustment(
    websocket: WebSocket,
    token: str = Query(...),
    project_id: str = Query(...),
    env_id: str = Query(...),
):
    """
    Local training processes connect here to receive adjustment instructions.
    
    Server sends:
      - type: "adjust_instruction"
        env_id, config, reason, rule_id, ...
    
    Client sends:
      - type: "heartbeat"
      - type: "adjust_ack"
    """
    try:
        payload = _validate_ws_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4003, reason="authentication failed")
        return

    await manager.connect_adjustment(project_id, env_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "heartbeat":
                manager.update_heartbeat(websocket)
                await websocket.send_json({"type": "heartbeat_ack"})
                continue

            if msg_type == "adjust_ack":
                manager.update_heartbeat(websocket)
                logger.info(f"Adjustment acknowledged by training process: {project_id}:{env_id}")
                continue

            if msg_type == "status_report":
                # Training process reports its current status
                manager.update_heartbeat(websocket)
                status_data = msg.get("data", {})
                # Broadcast status to frontend
                await manager.broadcast_notification(project_id, {
                    "level": "info",
                    "title": "Training Status",
                    "message": f"Env {env_id}: {status_data.get('status', 'unknown')}",
                    "data": status_data,
                })
                continue

            await websocket.send_json({
                "type": "error",
                "detail": f"Unknown message type: {msg_type}",
            })

    except WebSocketDisconnect:
        logger.info(f"Adjustment WS disconnected normally: {project_id}:{env_id}")
    except Exception as e:
        logger.error(f"Adjustment WS error: {e}")
    finally:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# WebSocket 3: /ws/frontend — browser frontend receives real-time updates
# ---------------------------------------------------------------------------
@router.websocket("/ws/frontend")
async def ws_frontend(
    websocket: WebSocket,
    token: str = Query(...),
    project_id: str = Query(...),
):
    """
    Frontend browser connects here to receive real-time updates.
    
    Receives:
      - type: "metric_broadcast"
      - type: "notification"
      - type: "adjust_notification"
      - type: "eval_complete"
    
    Client sends:
      - type: "heartbeat"
      - type: "subscribe_env"  (data: { env_id })
      - type: "unsubscribe_env" (data: { env_id })
    """
    try:
        payload = _validate_ws_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4003, reason="authentication failed")
        return

    await manager.connect_frontend(project_id, websocket)

    # Send connection confirmation
    try:
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "user_id": user_id,
            "server_stats": manager.stats,
        })
    except Exception:
        manager.disconnect(websocket)
        return

    # Track which env_ids this frontend is subscribed to
    subscribed_envs: set[str] = set()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "heartbeat":
                manager.update_heartbeat(websocket)
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "server_stats": manager.stats,
                })
                continue

            if msg_type == "subscribe_env":
                env_id = msg.get("data", {}).get("env_id")
                if env_id:
                    subscribed_envs.add(env_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "env_id": env_id,
                    })
                continue

            if msg_type == "unsubscribe_env":
                env_id = msg.get("data", {}).get("env_id")
                if env_id and env_id in subscribed_envs:
                    subscribed_envs.discard(env_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "env_id": env_id,
                    })
                continue

            if msg_type == "request_stats":
                await websocket.send_json({
                    "type": "server_stats",
                    "data": manager.stats,
                })
                continue

            await websocket.send_json({
                "type": "error",
                "detail": f"Unknown message type: {msg_type}",
            })

    except WebSocketDisconnect:
        logger.info(f"Frontend WS disconnected normally: project={project_id}")
    except Exception as e:
        logger.error(f"Frontend WS error: {e}")
    finally:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Convenience functions for other services to push data via WebSocket
# ---------------------------------------------------------------------------
async def push_metric_to_frontend(project_id: str, env_id: str, data: dict):
    """Helper used by other services to push metrics to frontend."""
    await manager.broadcast_metrics(project_id, env_id, data)


async def push_notification_to_frontend(project_id: str, notification: dict):
    """Helper used by other services to push notifications to frontend."""
    await manager.broadcast_notification(project_id, notification)


async def push_adjustment_to_training(project_id: str, env_id: str, instruction: dict):
    """Helper used by other services to push adjustments to training process."""
    await manager.send_adjustment(project_id, env_id, instruction)


async def push_eval_result_to_frontend(project_id: str, env_id: str, eval_data: dict):
    """Push evaluation result to frontend connections."""
    if project_id in manager.frontend_connections:
        for ws in manager.frontend_connections[project_id][:]:
            try:
                await ws.send_json({
                    "type": "eval_complete",
                    "env_id": env_id,
                    "data": eval_data,
                })
            except Exception:
                manager.frontend_connections[project_id].remove(ws)
