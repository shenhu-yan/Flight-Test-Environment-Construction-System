import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    creator: Mapped["User"] = relationship("User", back_populates="projects_created", lazy="selectin")
    members: Mapped[list["ProjectRole"]] = relationship("ProjectRole", back_populates="project", lazy="selectin")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", lazy="selectin")
    envs: Mapped[list["Env"]] = relationship("Env", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"
