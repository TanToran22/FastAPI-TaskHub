"""task_project_not_null_and_composite_indexes

Revision ID: 0002_task_comment_idx
Revises: 0001_initial
Create Date: 2026-04-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_task_comment_idx"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "tasks",
        "project_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_index(op.f("ix_tasks_project_id"), table_name="tasks")
    op.create_index(
        "ix_tasks_project_created_id",
        "tasks",
        ["project_id", "created_at", "id"],
        unique=False,
    )
    op.drop_index(op.f("ix_comments_task_id"), table_name="comments")
    op.create_index(
        "ix_comments_task_created_at",
        "comments",
        ["task_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comments_task_created_at", table_name="comments")
    op.create_index(
        op.f("ix_comments_task_id"),
        "comments",
        ["task_id"],
        unique=False,
    )
    op.drop_index("ix_tasks_project_created_id", table_name="tasks")
    op.create_index(
        op.f("ix_tasks_project_id"),
        "tasks",
        ["project_id"],
        unique=False,
    )
    op.alter_column(
        "tasks",
        "project_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
