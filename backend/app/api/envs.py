import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_member, require_project_configurer
from app.services.config_parser import parse_json_config, parse_xml_config
from app.services.env_generator import generate_scene_data
from app.tasks.env_tasks import generate_env_task

router = APIRouter()


@router.get("")
async def get_envs(
    project_id: str = None,
    task_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, project_id, task_id, name, status, created_at FROM envs WHERE status != 'deprecated'"
    params = {}

    if project_id:
        query += " AND project_id = :project_id"
        params["project_id"] = project_id
    if task_id:
        query += " AND task_id = :task_id"
        params["task_id"] = task_id

    query += " ORDER BY created_at DESC"

    result = await db.execute(text(query), params)
    envs = result.fetchall()
    return {
        "code": 0,
        "data": [
            {"id": e[0], "project_id": e[1], "task_id": e[2], "name": e[3], "status": e[4], "created_at": str(e[5]) if e[5] else None}
            for e in envs
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_env(
    env_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project_id = env_data.get("project_id")
    if not project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

    env_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO envs (id, project_id, task_id, name, config, template_id, status, created_by, created_at)
            VALUES (:id, :project_id, :task_id, :name, :config, :template_id, 'generating', :created_by, NOW())
            """
        ),
        {
            "id": env_id,
            "project_id": project_id,
            "task_id": env_data.get("task_id"),
            "name": env_data.get("name", "New Environment"),
            "config": json.dumps(env_data.get("config", {})),
            "template_id": env_data.get("template_id"),
            "created_by": current_user["id"],
        }
    )

    try:
        generate_env_task.delay(
            env_id,
            env_data.get("config", {}),
            project_id,
            current_user["id"]
        )
    except Exception:
        # If Celery is not available, mark as active directly
        await db.execute(
            text("UPDATE envs SET status = 'active', updated_at = NOW() WHERE id = :id"),
            {"id": env_id}
        )

    return {"code": 0, "data": {"id": env_id, "status": "generating"}}


@router.get("/{env_id}")
async def get_env(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, project_id, task_id, name, config, status, storage_path, created_at FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    return {
        "code": 0,
        "data": {
            "id": env[0],
            "project_id": env[1],
            "task_id": env[2],
            "name": env[3],
            "config": json.loads(env[4]) if isinstance(env[4], str) else env[4],
            "status": env[5],
            "storage_path": env[6],
            "created_at": str(env[7]) if env[7] else None,
        }
    }


@router.delete("/{env_id}")
async def delete_env(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    await db.execute(
        text("UPDATE envs SET status = 'deprecated', updated_at = NOW() WHERE id = :id"),
        {"id": env_id}
    )
    return {"code": 0, "message": "Environment deleted successfully"}


@router.post("/parse-config")
async def parse_config(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    content = await file.read()
    content_str = content.decode("utf-8")

    try:
        if file.filename.endswith(".json"):
            config = parse_json_config(content_str)
        elif file.filename.endswith(".xml"):
            config = parse_xml_config(content_str)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file format")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return {"code": 0, "data": config.model_dump()}


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_envs(
    batch_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    base_config = batch_data.get("config", {})
    count = batch_data.get("count", 1)
    project_id = batch_data.get("project_id")

    if not project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

    env_ids = []
    for i in range(count):
        config = base_config.copy()
        if "atmosphere" in config:
            import random
            config["atmosphere"]["wind_speed"] = config["atmosphere"].get("wind_speed", 5) + random.uniform(-2, 2)
            config["atmosphere"]["wind_direction"] = (config["atmosphere"].get("wind_direction", 90) + random.uniform(-30, 30)) % 360

        env_id = str(uuid.uuid4())
        await db.execute(
            text(
                """
                INSERT INTO envs (id, project_id, name, config, status, created_by, created_at)
                VALUES (:id, :project_id, :name, :config, 'generating', :created_by, NOW())
                """
            ),
            {
                "id": env_id,
                "project_id": project_id,
                "name": f"Batch Environment {i+1}",
                "config": json.dumps(config),
                "created_by": current_user["id"],
            }
        )
        env_ids.append(env_id)

        generate_env_task.delay(env_id, config, project_id, current_user["id"])

    return {"code": 0, "data": {"env_ids": env_ids, "count": count}}


@router.post("/import")
async def import_env(
    file: UploadFile = File(...),
    project_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import zipfile
    import tempfile
    import os
    from minio import Minio
    from io import BytesIO

    content = await file.read()

    try:
        zip_buffer = BytesIO(content)
        with zipfile.ZipFile(zip_buffer, 'r') as zipf:
            config_file = None
            for name in zipf.namelist():
                if name.endswith("config.json"):
                    config_file = zipf.read(name)
                    break

            if not config_file:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zip file: missing config.json")

            config = json.loads(config_file)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zip file")

    env_id = str(uuid.uuid4())

    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )

    bucket_name = settings.MINIO_BUCKET
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    storage_path = f"envs/{project_id}/{env_id}.zip"
    minio_client.put_object(
        bucket_name,
        storage_path,
        BytesIO(content),
        length=len(content),
        content_type="application/zip",
    )

    await db.execute(
        text(
            """
            INSERT INTO envs (id, project_id, name, config, status, storage_path, created_by, created_at)
            VALUES (:id, :project_id, :name, :config, 'active', :storage_path, :created_by, NOW())
            """
        ),
        {
            "id": env_id,
            "project_id": project_id,
            "name": f"Imported Environment",
            "config": json.dumps(config),
            "storage_path": storage_path,
            "created_by": current_user["id"],
        }
    )

    return {"code": 0, "data": {"id": env_id, "status": "active"}}


@router.get("/{env_id}/export")
async def export_env(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from fastapi.responses import StreamingResponse
    from minio import Minio

    result = await db.execute(
        text("SELECT storage_path, name FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )

    try:
        response = minio_client.get_object(settings.MINIO_BUCKET, env[0])
        return StreamingResponse(
            response.stream,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={env[1]}.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment file not found")


@router.get("/{env_id}/export-json")
async def export_env_json(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """导出环境配置为JSON格式"""
    from fastapi.responses import Response

    result = await db.execute(
        text("SELECT id, project_id, name, config, status, created_at FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    config = json.loads(env[3]) if isinstance(env[3], str) else env[3]

    export_data = {
        "version": "1.0",
        "exported_at": str(env[5]) if env[5] else None,
        "environment": {
            "id": env[0],
            "project_id": env[1],
            "name": env[2],
            "status": env[4],
        },
        "config": config
    }

    json_content = json.dumps(export_data, indent=2, ensure_ascii=False)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{env[2]}.json"'}
    )


@router.get("/{env_id}/preview")
async def get_preview(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import zipfile
    import os
    import numpy as np

    result = await db.execute(
        text("SELECT storage_path, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    storage_path = env[0]
    config = json.loads(env[1]) if isinstance(env[1], str) else env[1]

    # If no storage path, generate preview from config
    if not storage_path or not os.path.exists(storage_path):
        import numpy as np

        terrain = config.get("terrain", {})
        atmosphere = config.get("atmosphere", {})
        obstacles = config.get("obstacles", {})
        waypoints = config.get("waypoints", [])

        grid_size = [100, 100]
        elevation = np.random.uniform(
            terrain.get("elevation_min", 0),
            terrain.get("elevation_max", 100),
            (grid_size[1], grid_size[0])
        ).tolist()

        obstacle_list = []
        for i in range(obstacles.get("count", 0)):
            obstacle_list.append({
                "type": obstacles.get("types", ["building"])[i % len(obstacles.get("types", ["building"]))] if obstacles.get("types") else "building",
                "position": [float(np.random.uniform(0, 500)), float(np.random.uniform(0, 500)), 0],
                "size": [10, 10, 20],
            })

        waypoint_list = []
        for wp in waypoints:
            waypoint_list.append({
                "id": wp.get("id", ""),
                "position": wp.get("position", [0, 0, 100]),
                "order": wp.get("order", 1),
            })

        scene_data = {
            "terrain": {
                "grid_size": grid_size,
                "resolution": terrain.get("resolution", 1.0),
                "elevation": elevation,
            },
            "obstacles": obstacle_list,
            "waypoints": waypoint_list,
            "wind": {
                "direction": [1.0, 0.5, 0.0],
                "speed": atmosphere.get("wind_speed", 5),
                "variability": 0.3,
            },
            "runway": {
                "position": [0, 0, 0],
                "heading": 90,
                "length": 3000,
                "width": 60,
            }
        }
        return {"code": 0, "data": scene_data}

    try:
        with zipfile.ZipFile(storage_path, 'r') as zipf:
            for name in zipf.namelist():
                if name.endswith("scene.json"):
                    scene_data = json.loads(zipf.read(name))
                    return {"code": 0, "data": scene_data}

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview data not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview data not found")


@router.post("/{env_id}/adjust")
async def adjust_env(
    env_id: str,
    adjust_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.services.ws_manager import send_adjustment_instruction

    result = await db.execute(
        text("SELECT id, project_id, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    config = json.loads(env[2]) if isinstance(env[2], str) else env[2]

    snapshot_before_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
            VALUES (:id, :env_id, :config, 'manual_adjust', :operator, :reason, NOW())
            """
        ),
        {
            "id": snapshot_before_id,
            "env_id": env_id,
            "config": json.dumps(config),
            "operator": current_user["id"],
            "reason": adjust_data.get("reason", "手动调整"),
        }
    )

    for key, value in adjust_data.get("params", {}).items():
        parts = key.split(".")
        if len(parts) == 2:
            section, param = parts
            if section in config and param in config[section]:
                config[section][param] = value

    await db.execute(
        text("UPDATE envs SET config = :config, updated_at = NOW() WHERE id = :id"),
        {"id": env_id, "config": json.dumps(config)}
    )

    snapshot_after_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
            VALUES (:id, :env_id, :config, 'manual_adjust', :operator, :reason, NOW())
            """
        ),
        {
            "id": snapshot_after_id,
            "env_id": env_id,
            "config": json.dumps(config),
            "operator": current_user["id"],
            "reason": f"调整后: {adjust_data.get('reason', '手动调整')}",
        }
    )

    await db.execute(
        text(
            """
            INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, operator, created_at)
            VALUES (:id, :env_id, :snapshot_before, :snapshot_after, 'manual', :operator, NOW())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "env_id": env_id,
            "snapshot_before": snapshot_before_id,
            "snapshot_after": snapshot_after_id,
            "operator": current_user["id"],
        }
    )

    await send_adjustment_instruction(env[1], env_id, {
        "type": "adjust_instruction",
        "strategy": "manual",
        "new_config": config,
    })

    return {"code": 0, "message": "Environment adjusted successfully"}


@router.post("/{env_id}/rollback")
async def rollback_env(
    env_id: str,
    rollback_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.services.ws_manager import send_adjustment_instruction

    snapshot_id = rollback_data.get("snapshot_id")
    if not snapshot_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="snapshot_id is required")

    snapshot_result = await db.execute(
        text("SELECT config FROM env_snapshots WHERE id = :id AND env_id = :env_id"),
        {"id": snapshot_id, "env_id": env_id}
    )
    snapshot = snapshot_result.fetchone()
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")

    env_result = await db.execute(
        text("SELECT id, project_id, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = env_result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    current_config = json.loads(env[2]) if isinstance(env[2], str) else env[2]

    before_snapshot_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
            VALUES (:id, :env_id, :config, 'manual_adjust', :operator, :reason, NOW())
            """
        ),
        {
            "id": before_snapshot_id,
            "env_id": env_id,
            "config": json.dumps(current_config),
            "operator": current_user["id"],
            "reason": f"回滚前状态",
        }
    )

    rollback_config = json.loads(snapshot[0]) if isinstance(snapshot[0], str) else snapshot[0]
    await db.execute(
        text("UPDATE envs SET config = :config, updated_at = NOW() WHERE id = :id"),
        {"id": env_id, "config": json.dumps(rollback_config)}
    )

    after_snapshot_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
            VALUES (:id, :env_id, :config, 'manual_adjust', :operator, :reason, NOW())
            """
        ),
        {
            "id": after_snapshot_id,
            "env_id": env_id,
            "config": json.dumps(rollback_config),
            "operator": current_user["id"],
            "reason": f"回滚至快照 {snapshot_id}",
        }
    )

    await db.execute(
        text(
            """
            INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, operator, created_at)
            VALUES (:id, :env_id, :snapshot_before, :snapshot_after, 'manual', :operator, NOW())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "env_id": env_id,
            "snapshot_before": before_snapshot_id,
            "snapshot_after": after_snapshot_id,
            "operator": current_user["id"],
        }
    )

    await send_adjustment_instruction(env[1], env_id, {
        "type": "adjust_instruction",
        "strategy": "rollback",
        "new_config": rollback_config,
    })

    return {"code": 0, "message": "Environment rolled back successfully"}


@router.get("/{env_id}/snapshots")
async def get_snapshots(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, env_id, config, trigger_type, operator, reason, created_at
            FROM env_snapshots WHERE env_id = :env_id
            ORDER BY created_at DESC
            """
        ),
        {"env_id": env_id}
    )
    snapshots = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": s[0],
                "env_id": s[1],
                "config": json.loads(s[2]) if isinstance(s[2], str) else s[2],
                "trigger_type": s[3],
                "operator": s[4],
                "reason": s[5],
                "created_at": str(s[6]) if s[6] else None,
            }
            for s in snapshots
        ]
    }


@router.get("/{env_id}/adjustment-history")
async def get_adjustment_history(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, operator, created_at
            FROM adjustment_history WHERE env_id = :env_id
            ORDER BY created_at DESC
            """
        ),
        {"env_id": env_id}
    )
    history = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": h[0],
                "env_id": h[1],
                "snapshot_before": h[2],
                "snapshot_after": h[3],
                "trigger_type": h[4],
                "trigger_rule": h[5],
                "operator": h[6],
                "created_at": str(h[7]) if h[7] else None,
            }
            for h in history
        ]
    }


@router.post("/{env_id}/train")
async def start_training(
    env_id: str,
    training_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.services.training_service import training_service

    result = await db.execute(
        text("SELECT id, project_id, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    config = json.loads(env[2]) if isinstance(env[2], str) else env[2]
    max_steps = training_data.get("max_steps", 1000)

    training_result = await training_service.start_training(
        env_id=env_id,
        project_id=env[1],
        config=config,
        max_steps=max_steps,
        user_id=current_user["id"]
    )

    return {"code": 0, "data": training_result}


@router.post("/{env_id}/stop-training")
async def stop_training(
    env_id: str,
    current_user: dict = Depends(get_current_user)
):
    from app.services.training_service import training_service

    for training_id, training in training_service.active_trainings.items():
        if training["env_id"] == env_id and training["status"] == "running":
            training_service.stop_training(training_id)
            return {"code": 0, "message": "Training stopped"}

    return {"code": 0, "message": "No active training found"}


@router.get("/{env_id}/training-status")
async def get_training_status(
    env_id: str,
    current_user: dict = Depends(get_current_user)
):
    from app.services.training_service import training_service

    for training_id, training in training_service.active_trainings.items():
        if training["env_id"] == env_id:
            return {
                "code": 0,
                "data": {
                    "training_id": training_id,
                    "status": training["status"],
                    "current_step": training["current_step"],
                    "max_steps": training["max_steps"],
                    "progress": training["current_step"] / training["max_steps"] * 100,
                    "latest_metrics": training["metrics_history"][-1] if training["metrics_history"] else None,
                }
            }

    return {"code": 0, "data": None}


@router.get("/{env_id}/metrics")
async def get_training_metrics(
    env_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, episode_reward, success_rate, convergence_speed, step, reported_at
            FROM training_metrics WHERE env_id = :env_id
            ORDER BY step ASC
            LIMIT :limit
            """
        ),
        {"env_id": env_id, "limit": limit}
    )
    metrics = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": m[0],
                "episode_reward": m[1],
                "success_rate": m[2],
                "convergence_speed": m[3],
                "step": m[4],
                "reported_at": str(m[5]) if m[5] else None,
            }
            for m in metrics
        ]
    }
