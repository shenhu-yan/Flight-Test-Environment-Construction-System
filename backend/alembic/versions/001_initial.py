"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('global_role', sa.String(16), default='viewer'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'project_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
    )

    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('aircraft_type', sa.String(32), nullable=False),
        sa.Column('difficulty', sa.String(16), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('is_builtin', sa.Boolean, default=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('condition', postgresql.JSONB, nullable=False),
        sa.Column('action', postgresql.JSONB, nullable=False),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'envs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('template_id', sa.String(36), sa.ForeignKey('templates.id')),
        sa.Column('status', sa.String(16), default='generating'),
        sa.Column('storage_path', sa.String(256)),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'env_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('env_id', sa.String(36), sa.ForeignKey('envs.id'), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('trigger_type', sa.String(16), nullable=False),
        sa.Column('operator', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('reason', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'adjustment_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('env_id', sa.String(36), sa.ForeignKey('envs.id'), nullable=False),
        sa.Column('snapshot_before', sa.String(36), sa.ForeignKey('env_snapshots.id')),
        sa.Column('snapshot_after', sa.String(36), sa.ForeignKey('env_snapshots.id')),
        sa.Column('trigger_type', sa.String(16), nullable=False),
        sa.Column('trigger_rule', sa.String(36), sa.ForeignKey('strategies.id')),
        sa.Column('operator', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('metric_change', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'env_evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('env_id', sa.String(36), sa.ForeignKey('envs.id'), nullable=False),
        sa.Column('diversity_score', sa.Float),
        sa.Column('challenge_score', sa.Float),
        sa.Column('realism_score', sa.Float),
        sa.Column('effectiveness_score', sa.Float),
        sa.Column('total_score', sa.Float),
        sa.Column('weights', postgresql.JSONB),
        sa.Column('suggestions', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'training_metrics',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('env_id', sa.String(36), sa.ForeignKey('envs.id'), nullable=False),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('episode_reward', sa.Float),
        sa.Column('success_rate', sa.Float),
        sa.Column('convergence_speed', sa.Float),
        sa.Column('step', sa.Integer),
        sa.Column('reported_at', sa.DateTime),
    )

    op.create_table(
        'models',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('status', sa.String(16), default='active'),
        sa.Column('description', sa.Text),
        sa.Column('current_version', sa.String(20), default='1.0.0'),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_id', sa.String(36), sa.ForeignKey('models.id'), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('storage_path', sa.String(256)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('download_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'optimization_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('param_space', postgresql.JSONB),
        sa.Column('weights', postgresql.JSONB),
        sa.Column('max_iterations', sa.Integer),
        sa.Column('current_iteration', sa.Integer, default=0),
        sa.Column('status', sa.String(16), default='pending'),
        sa.Column('best_params', postgresql.JSONB),
        sa.Column('best_score', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'optimization_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('optimization_tasks.id'), nullable=False),
        sa.Column('before_scores', postgresql.JSONB),
        sa.Column('after_scores', postgresql.JSONB),
        sa.Column('comparison_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(16), default='info'),
        sa.Column('title', sa.String(128), nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('read', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'operation_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('resource_type', sa.String(32)),
        sa.Column('resource_id', sa.String(36)),
        sa.Column('detail', postgresql.JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'system_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('level', sa.String(16), nullable=False),
        sa.Column('module', sa.String(64)),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('detail', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table('system_logs')
    op.drop_table('operation_logs')
    op.drop_table('notifications')
    op.drop_table('optimization_reports')
    op.drop_table('optimization_tasks')
    op.drop_table('model_versions')
    op.drop_table('models')
    op.drop_table('training_metrics')
    op.drop_table('env_evaluations')
    op.drop_table('adjustment_history')
    op.drop_table('env_snapshots')
    op.drop_table('envs')
    op.drop_table('strategies')
    op.drop_table('templates')
    op.drop_table('tasks')
    op.drop_table('project_roles')
    op.drop_table('projects')
    op.drop_table('users')
