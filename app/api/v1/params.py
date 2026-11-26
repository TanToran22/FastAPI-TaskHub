from typing import Annotated

from fastapi import Path, Query

from app.models.enums import ProjectStatus, TaskPriority, TaskStatus

WorkspaceIdPath = Annotated[int, Path(gt=0, description="Workspace ID")]
UserIdPath = Annotated[int, Path(gt=0, description="Target User ID")]
ProjectIdPath = Annotated[int, Path(gt=0, description="Project ID")]
TaskIdPath = Annotated[int, Path(gt=0, description="Task ID")]
LabelIdPath = Annotated[int, Path(gt=0, description="Label ID")]
CommentIdPath = Annotated[int, Path(gt=0, description="Comment ID")]

ProjectStatusQuery = Annotated[
    ProjectStatus | None,
    Query(
        alias="status",
        description="Optional filter by project status (ACTIVE/ARCHIVED)",
    ),
]
TaskStatusFilterQuery = Annotated[
    list[TaskStatus] | None,
    Query(
        alias="status",
        description="Filter tasks by one or more statuses",
    ),
]
TaskPriorityFilterQuery = Annotated[
    list[TaskPriority] | None,
    Query(
        alias="priority",
        description="Filter tasks by one or more priorities",
    ),
]
AssigneeIdFilterQuery = Annotated[
    int | None,
    Query(gt=0, description="Filter tasks by assignee user ID"),
]
