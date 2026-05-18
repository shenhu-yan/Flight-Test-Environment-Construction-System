"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("global_role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "project_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("aircraft_type", sa.String(64), nullable=False),
        sa.Column("difficulty", sa.String(32), nullable=False, server_default="basic"),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "envs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("config", JSONB(), nullable=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft", index=True),
        sa.Column("storage_path", sa.String(512), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "strategy_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("condition_config", JSONB(), nullable=False),
        sa.Column("action_config", JSONB(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "env_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("env_id", sa.String(36), sa.ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("operator", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "adjustment_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("env_id", sa.String(36), sa.ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("snapshot_before", sa.String(36), sa.ForeignKey("env_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snapshot_after", sa.String(36), sa.ForeignKey("env_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("trigger_rule", sa.String(36), sa.ForeignKey("strategy_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operator", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metric_change", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "env_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("env_id", sa.String(36), sa.ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("diversity_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("challenge_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("realism_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("effectiveness_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("total_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("weights", JSONB(), nullable=True),
        sa.Column("suggestions", JSONB(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "training_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("env_id", sa.String(36), sa.ForeignKey("envs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("episode_reward", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("convergence_speed", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("step", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("reported_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "models_table",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft", index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("models_table.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "optimization_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("param_space", JSONB(), nullable=False),
        sa.Column("weights", JSONB(), nullable=False),
        sa.Column("max_iterations", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("current_iteration", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("params", JSONB(), nullable=True),
        sa.Column("best_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "optimization_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("optimization_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("before_scores", JSONB(), nullable=False),
        sa.Column("after_scores", JSONB(), nullable=False),
        sa.Column("comparison_data", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(32), nullable=False, server_default="info"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("detail", JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "system_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("module", sa.String(128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_logs")
    op.drop_table("operation_logs")
    op.drop_table("notifications")
    op.drop_table("optimization_reports")
    op.drop_table("optimization_tasks")
    op.drop_table("model_versions")
    op.drop_table("models_table")
    op.drop_table("training_metrics")
    op.drop_table("env_evaluations")
    op.drop_table("adjustment_history")
    op.drop_table("env_snapshots")
    op.drop_table("strategy_rules")
    op.drop_table("envs")
    op.drop_table("templates")
    op.drop_table("tasks")
    op.drop_table("project_roles")
    op.drop_table("projects")
    op.drop_table("users")
