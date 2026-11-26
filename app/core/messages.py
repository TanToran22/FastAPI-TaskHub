MSG_TASK_NOT_FOUND = "Task not found."
MSG_USER_NOT_FOUND = "User not found."
MSG_WORKSPACE_NOT_FOUND = "Workspace not found."
MSG_WORKSPACE_MEMBER_NOT_FOUND = "Workspace member not found."
MSG_PROJECT_NOT_FOUND = "Project not found."
MSG_LABEL_NOT_FOUND = "Label not found."
MSG_COMMENT_NOT_FOUND = "Comment not found."

MSG_FIELD_CANNOT_BE_NULL = "Field '{field_name}' cannot be null if provided."
MSG_DUE_DATE_IN_PAST = "due_date cannot be in the past."
MSG_FOREIGN_KEY_VIOLATION = (
    "Foreign key constraint violation: referenced resource does not exist."
)
MSG_INTEGRITY_ERROR = "Database integrity constraint violation."

# Auth & RBAC messages
MSG_EMAIL_ALREADY_EXISTS = "A user with this email already exists."
MSG_INVALID_CREDENTIALS = "Incorrect email or password."
MSG_INVALID_TOKEN = "Could not validate credentials or token has expired."
MSG_INVALID_REFRESH_TOKEN = "Invalid or expired refresh token."
MSG_INACTIVE_USER = "User account is inactive."
MSG_FORBIDDEN_ADMIN_ONLY = "The user does not have sufficient privileges."
MSG_INCORRECT_CURRENT_PASSWORD = "Incorrect current password."
MSG_PASSWORD_TOO_LONG_BYTES = "Password must not exceed 72 bytes when encoded in UTF-8."

# Workspace, Project, Task, Label & Comment messages
MSG_WORKSPACE_FORBIDDEN = "You do not have permission to perform this action."
MSG_WORKSPACE_MEMBER_ALREADY_EXISTS = "User is already a member of this workspace."
MSG_CANNOT_REMOVE_WORKSPACE_OWNER = "Cannot remove the workspace owner."
MSG_CANNOT_MODIFY_OWNER_ROLE = "Cannot change the workspace owner's role."
MSG_PROJECT_ARCHIVED = "Project is archived and cannot be modified."
MSG_PROJECT_ALREADY_ARCHIVED = "Project is already archived."
MSG_PROJECT_NOT_ARCHIVED = "Project is not archived."
MSG_ASSIGNEE_NOT_WORKSPACE_MEMBER = "Assignee must be a member of the workspace."
MSG_LABEL_ALREADY_EXISTS = "A label with this name already exists in project."
MSG_TASK_LABEL_ALREADY_ASSIGNED = "Label is already assigned to this task."
MSG_TASK_LABEL_NOT_ASSIGNED = "Label is not assigned to this task."
MSG_COMMENT_FORBIDDEN = (
    "Only the comment author with write access, workspace owner, "
    "or admin can modify this comment."
)
