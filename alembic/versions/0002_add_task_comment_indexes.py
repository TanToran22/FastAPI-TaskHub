"""add_task_comment_indexes

Revision ID: 0002_task_comment_idx
Revises: 0001_initial
Create Date: 2026-04-02 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_task_comment_idx"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_project_status",
        "tasks",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_comments_task_created_at",
        "comments",
        ["task_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comments_task_created_at", table_name="comments")
    op.drop_index("ix_tasks_project_status", table_name="tasks")
