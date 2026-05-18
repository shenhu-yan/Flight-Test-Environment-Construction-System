import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Text, Float, Integer, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Env(Base):
    __tablename__ = "envs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="envs", lazy="selectin")
    task: Mapped["Task | None"] = relationship("Task", back_populates="envs", lazy="selectin")
    snapshots: Mapped[list["EnvSnapshot"]] = relationship("EnvSnapshot", back_populates="env", lazy="selectin")
    evaluations: Mapped[list["EnvEvaluation"]] = relationship("EnvEvaluation", back_populates="env", lazy="selectin")
    training_metrics: Mapped[list["TrainingMetric"]] = relationship("TrainingMetric", back_populates="env", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Env(id={self.id}, name={self.name}, status={self.status})>"


class EnvSnapshot(Base):
    __tablename__ = "env_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    env_id: Mapped[str] = mapped_column(String(36), ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    operator: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    env: Mapped["Env"] = relationship("Env", back_populates="snapshots", lazy="selectin")


class AdjustmentHistory(Base):
    __tablename__ = "adjustment_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    env_id: Mapped[str] = mapped_column(String(36), ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_before: Mapped[str | None] = mapped_column(String(36), ForeignKey("env_snapshots.id", ondelete="SET NULL"), nullable=True)
    snapshot_after: Mapped[str | None] = mapped_column(String(36), ForeignKey("env_snapshots.id", ondelete="SET NULL"), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_rule: Mapped[str | None] = mapped_column(String(36), ForeignKey("strategy_rules.id", ondelete="SET NULL"), nullable=True)
    operator: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metric_change: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class EnvEvaluation(Base):
    __tablename__ = "env_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    env_id: Mapped[str] = mapped_column(String(36), ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True)
    diversity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    challenge_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    realism_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    effectiveness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    env: Mapped["Env"] = relationship("Env", back_populates="evaluations", lazy="selectin")


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    env_id: Mapped[str] = mapped_column(String(36), ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    episode_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    convergence_speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    env: Mapped["Env"] = relationship("Env", back_populates="training_metrics", lazy="selectin")


class StrategyRule(Base):
    __tablename__ = "strategy_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    condition_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
