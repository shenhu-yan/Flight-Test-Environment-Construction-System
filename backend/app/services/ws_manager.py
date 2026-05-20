import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.metrics_connections: dict[str, WebSocket] = {}
        self.adjustment_connections: dict[str, WebSocket] = {}
        self.frontend_connections: dict[str, list[WebSocket]] = {}

    async def register_metrics(self, key: str, websocket: WebSocket):
        self.metrics_connections[key] = websocket

    async def unregister_metrics(self, key: str):
        self.metrics_connections.pop(key, None)

    async def register_adjustment(self, key: str, websocket: WebSocket):
        self.adjustment_connections[key] = websocket

    async def unregister_adjustment(self, key: str):
        self.adjustment_connections.pop(key, None)

    async def register_frontend(self, project_id: str, websocket: WebSocket):
        if project_id not in self.frontend_connections:
            self.frontend_connections[project_id] = []
        self.frontend_connections[project_id].append(websocket)

    async def unregister_frontend(self, project_id: str, websocket: WebSocket):
        if project_id in self.frontend_connections:
            self.frontend_connections[project_id] = [
                ws for ws in self.frontend_connections[project_id] if ws != websocket
            ]
            if not self.frontend_connections[project_id]:
                del self.frontend_connections[project_id]

    async def broadcast_metrics(self, project_id: str, data: dict):
        if project_id in self.frontend_connections:
            message = json.dumps({"type": "metric_broadcast", "data": data})
            for ws in self.frontend_connections[project_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

    async def send_adjustment(self, key: str, instruction: dict):
        if key in self.adjustment_connections:
            message = json.dumps({"type": "adjust_instruction", "data": instruction})
            try:
                await self.adjustment_connections[key].send_text(message)
            except Exception:
                pass

    async def broadcast_notification(self, project_id: str, notification: dict):
        if project_id in self.frontend_connections:
            message = json.dumps({"type": "notification", "data": notification})
            for ws in self.frontend_connections[project_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def send_adjustment_instruction(project_id: str, env_id: str, instruction: dict):
    key = f"{project_id}:{env_id}"
    await manager.send_adjustment(key, instruction)


async def send_notification(project_id: str, notification: dict):
    await manager.broadcast_notification(project_id, notification)
