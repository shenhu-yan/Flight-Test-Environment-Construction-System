import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))

    tasks = relationship("Task", back_populates="project")
    models = relationship("Model", back_populates="project")
    members = relationship("ProjectRole", back_populates="project")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))

    project = relationship("Project", back_populates="tasks")
    envs = relationship("Env", back_populates="task")


class Env(Base, TimestampMixin):
    __tablename__ = "envs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"))
    name = Column(String(128), nullable=False)
    config = Column(JSONB, nullable=False)
    template_id = Column(String(36), ForeignKey("templates.id"))
    status = Column(String(16), default="generating")
    storage_path = Column(String(256))
    created_by = Column(String(36), ForeignKey("users.id"))

    task = relationship("Task", back_populates="envs")
    snapshots = relationship("EnvSnapshot", back_populates="env")
    evaluations = relationship("EnvEvaluation", back_populates="env")
    training_metrics = relationship("TrainingMetric", back_populates="env")
    adjustment_history = relationship("AdjustmentHistory", back_populates="env")


class EnvSnapshot(Base, TimestampMixin):
    __tablename__ = "env_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    env_id = Column(String(36), ForeignKey("envs.id"), nullable=False)
    config = Column(JSONB, nullable=False)
    trigger_type = Column(String(16), nullable=False)
    operator = Column(String(36), ForeignKey("users.id"))
    reason = Column(Text)

    env = relationship("Env", back_populates="snapshots")


class AdjustmentHistory(Base, TimestampMixin):
    __tablename__ = "adjustment_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    env_id = Column(String(36), ForeignKey("envs.id"), nullable=False)
    snapshot_before = Column(String(36), ForeignKey("env_snapshots.id"))
    snapshot_after = Column(String(36), ForeignKey("env_snapshots.id"))
    trigger_type = Column(String(16), nullable=False)
    trigger_rule = Column(String(36), ForeignKey("strategies.id"))
    operator = Column(String(36), ForeignKey("users.id"))
    metric_change = Column(JSONB)

    env = relationship("Env", back_populates="adjustment_history")


class EnvEvaluation(Base, TimestampMixin):
    __tablename__ = "env_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    env_id = Column(String(36), ForeignKey("envs.id"), nullable=False)
    diversity_score = Column(Float)
    challenge_score = Column(Float)
    realism_score = Column(Float)
    effectiveness_score = Column(Float)
    total_score = Column(Float)
    weights = Column(JSONB)
    suggestions = Column(JSONB)

    env = relationship("Env", back_populates="evaluations")


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    env_id = Column(String(36), ForeignKey("envs.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"))
    episode_reward = Column(Float)
    success_rate = Column(Float)
    convergence_speed = Column(Float)
    step = Column(Integer)
    reported_at = Column(DateTime, default=datetime.utcnow)

    env = relationship("Env", back_populates="training_metrics")


class Model(Base, TimestampMixin):
    __tablename__ = "models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)
    status = Column(String(16), default="active")
    description = Column(Text)
    current_version = Column(String(20), default="1.0.0")
    created_by = Column(String(36), ForeignKey("users.id"))

    project = relationship("Project", back_populates="models")
    versions = relationship("ModelVersion", back_populates="model")


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False)
    version = Column(String(20), nullable=False)
    storage_path = Column(String(256))
    metadata_ = Column("metadata", JSONB)
    download_count = Column(Integer, default=0)

    model = relationship("Model", back_populates="versions")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    global_role = Column(String(16), default="viewer")

    project_roles = relationship("ProjectRole", back_populates="user")


class ProjectRole(Base):
    __tablename__ = "project_roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    role = Column(String(16), nullable=False)

    user = relationship("User", back_populates="project_roles")
    project = relationship("Project", back_populates="members")


class Template(Base, TimestampMixin):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    aircraft_type = Column(String(32), nullable=False)
    difficulty = Column(String(16), nullable=False)
    config = Column(JSONB, nullable=False)
    is_builtin = Column(Boolean, default=False)
    created_by = Column(String(36), ForeignKey("users.id"))


class Strategy(Base, TimestampMixin):
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    condition = Column(JSONB, nullable=False)
    action = Column(JSONB, nullable=False)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    project_id = Column(String(36), ForeignKey("projects.id"))


class OptimizationTask(Base, TimestampMixin):
    __tablename__ = "optimization_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    param_space = Column(JSONB)
    weights = Column(JSONB)
    max_iterations = Column(Integer)
    current_iteration = Column(Integer, default=0)
    status = Column(String(16), default="pending")
    best_params = Column(JSONB)
    best_score = Column(Float)

    reports = relationship("OptimizationReport", back_populates="task")


class OptimizationReport(Base, TimestampMixin):
    __tablename__ = "optimization_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("optimization_tasks.id"), nullable=False)
    before_scores = Column(JSONB)
    after_scores = Column(JSONB)
    comparison_data = Column(JSONB)

    task = relationship("OptimizationTask", back_populates="reports")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(16), default="info")
    title = Column(String(128), nullable=False)
    content = Column(Text)
    read = Column(Boolean, default=False)


class OperationLog(Base, TimestampMixin):
    __tablename__ = "operation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(32), nullable=False)
    resource_type = Column(String(32))
    resource_id = Column(String(36))
    detail = Column(JSONB)
    ip_address = Column(String(45))


class SystemLog(Base, TimestampMixin):
    __tablename__ = "system_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    level = Column(String(16), nullable=False)
    module = Column(String(64))
    message = Column(Text, nullable=False)
    detail = Column(JSONB)
