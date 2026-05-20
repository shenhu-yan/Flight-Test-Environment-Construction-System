import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_member, require_project_configurer
from app.core.config import settings

router = APIRouter()


@router.get("")
async def get_models(
    project_id: str = Query(None),
    type: str = Query(None),
    status_filter: str = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, project_id, name, type, status, description, current_version, created_by, created_at FROM models WHERE 1=1"
    params = {}

    if project_id:
        query += " AND project_id = :project_id"
        params["project_id"] = project_id
    if type:
        query += " AND type = :type"
        params["type"] = type
    if status_filter:
        query += " AND status = :status"
        params["status"] = status_filter

    query += " ORDER BY created_at DESC"

    result = await db.execute(text(query), params)
    models = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": m[0],
                "project_id": m[1],
                "name": m[2],
                "type": m[3],
                "status": m[4],
                "description": m[5],
                "current_version": m[6],
                "created_by": m[7],
                "created_at": str(m[8]) if m[8] else None,
            }
            for m in models
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_model(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    description: str = Form(None),
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    import os
    from datetime import datetime

    model_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    content = await file.read()

    local_storage = os.path.join(os.getcwd(), "storage", "models", project_id, model_id, "v1.0.0")
    os.makedirs(local_storage, exist_ok=True)

    storage_path = os.path.join(local_storage, file.filename)
    with open(storage_path, 'wb') as f:
        f.write(content)

    now = datetime.utcnow().isoformat()
    await db.execute(
        text(
            """
            INSERT INTO models (id, project_id, name, type, status, description, current_version, created_by, created_at)
            VALUES (:id, :project_id, :name, :type, 'active', :description, '1.0.0', :created_by, :now)
            """
        ),
        {
            "id": model_id,
            "project_id": project_id,
            "name": name,
            "type": type,
            "description": description,
            "created_by": current_user["id"],
            "now": now,
        }
    )

    await db.execute(
        text(
            """
            INSERT INTO model_versions (id, model_id, version, storage_path, metadata, created_at)
            VALUES (:id, :model_id, :version, :storage_path, :metadata, :now)
            """
        ),
        {
            "id": version_id,
            "model_id": model_id,
            "version": "1.0.0",
            "storage_path": storage_path,
            "metadata": json.dumps({"filename": file.filename, "size": len(content)}),
            "now": now,
        }
    )

    return {"code": 0, "data": {"id": model_id, "name": name, "version": "1.0.0"}}


@router.get("/{model_id}")
async def get_model(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, project_id, name, type, status, description, current_version, created_by, created_at FROM models WHERE id = :id"),
        {"id": model_id}
    )
    model = result.fetchone()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    return {
        "code": 0,
        "data": {
            "id": model[0],
            "project_id": model[1],
            "name": model[2],
            "type": model[3],
            "status": model[4],
            "description": model[5],
            "current_version": model[6],
            "created_by": model[7],
            "created_at": str(model[8]) if model[8] else None,
        }
    }


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM models WHERE id = :id"),
        {"id": model_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    await db.execute(
        text("UPDATE models SET status = 'deprecated', updated_at = NOW() WHERE id = :id"),
        {"id": model_id}
    )
    return {"code": 0, "message": "Model deleted successfully"}


@router.get("/{model_id}/versions")
async def get_versions(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, model_id, version, storage_path, metadata, download_count, created_at FROM model_versions WHERE model_id = :model_id ORDER BY created_at DESC"),
        {"model_id": model_id}
    )
    versions = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": v[0],
                "model_id": v[1],
                "version": v[2],
                "storage_path": v[3],
                "metadata": json.loads(v[4]) if isinstance(v[4], str) else v[4],
                "download_count": v[5],
                "created_at": str(v[6]) if v[6] else None,
            }
            for v in versions
        ]
    }


@router.post("/{model_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(
    model_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    import os
    from datetime import datetime

    model_result = await db.execute(
        text("SELECT id, project_id, current_version FROM models WHERE id = :id"),
        {"id": model_id}
    )
    model = model_result.fetchone()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    current_ver = model[2]
    parts = current_ver.split(".")
    parts[1] = str(int(parts[1]) + 1)
    new_version = ".".join(parts)

    version_id = str(uuid.uuid4())
    content = await file.read()

    local_storage = os.path.join(os.getcwd(), "storage", "models", model[1], model_id, new_version)
    os.makedirs(local_storage, exist_ok=True)

    storage_path = os.path.join(local_storage, file.filename)
    with open(storage_path, 'wb') as f:
        f.write(content)

    now = datetime.utcnow().isoformat()
    await db.execute(
        text(
            """
            INSERT INTO model_versions (id, model_id, version, storage_path, metadata, created_at)
            VALUES (:id, :model_id, :version, :storage_path, :metadata, :now)
            """
        ),
        {
            "id": version_id,
            "model_id": model_id,
            "version": new_version,
            "storage_path": storage_path,
            "metadata": json.dumps({"filename": file.filename, "size": len(content)}),
            "now": now,
        }
    )

    await db.execute(
        text("UPDATE models SET current_version = :version, updated_at = :now WHERE id = :id"),
        {"id": model_id, "version": new_version, "now": now}
    )

    return {"code": 0, "data": {"version": new_version}}


@router.post("/{model_id}/versions/diff")
async def diff_versions(
    model_id: str,
    version1: str = Query(...),
    version2: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result1 = await db.execute(
        text("SELECT version, metadata FROM model_versions WHERE model_id = :model_id AND version = :version"),
        {"model_id": model_id, "version": version1}
    )
    v1 = result1.fetchone()

    result2 = await db.execute(
        text("SELECT version, metadata FROM model_versions WHERE model_id = :model_id AND version = :version"),
        {"model_id": model_id, "version": version2}
    )
    v2 = result2.fetchone()

    if not v1 or not v2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    meta1 = json.loads(v1[1]) if isinstance(v1[1], str) else v1[1]
    meta2 = json.loads(v2[1]) if isinstance(v2[1], str) else v2[1]

    return {
        "code": 0,
        "data": {
            "version1": {"version": v1[0], "metadata": meta1},
            "version2": {"version": v2[0], "metadata": meta2},
        }
    }


@router.post("/{model_id}/rollback")
async def rollback_model(
    model_id: str,
    version: str = Query(...),
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM model_versions WHERE model_id = :model_id AND version = :version"),
        {"model_id": model_id, "version": version}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    await db.execute(
        text("UPDATE models SET current_version = :version, updated_at = NOW() WHERE id = :id"),
        {"id": model_id, "version": version}
    )

    return {"code": 0, "message": f"Rolled back to version {version}"}


@router.get("/{model_id}/versions/{ver}/download")
async def download_version(
    model_id: str,
    ver: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import os
    from fastapi.responses import FileResponse

    result = await db.execute(
        text("SELECT storage_path FROM model_versions WHERE model_id = :model_id AND version = :version"),
        {"model_id": model_id, "version": ver}
    )
    version = result.fetchone()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    storage_path = version[0]
    if not os.path.exists(storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(
        path=storage_path,
        media_type="application/octet-stream",
        filename=os.path.basename(storage_path)
    )
