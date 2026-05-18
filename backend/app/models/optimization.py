import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OptimizationTask(Base):
    __tablename__ = "optimization_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    param_space: Mapped[dict] = mapped_column(JSON, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    max_iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    current_iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<OptimizationTask(id={self.id}, status={self.status})>"


class OptimizationReport(Base):
    __tablename__ = "optimization_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("optimization_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    before_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    comparison_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<OptimizationReport(id={self.id}, task_id={self.task_id})>"
