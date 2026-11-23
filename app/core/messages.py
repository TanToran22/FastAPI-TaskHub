MSG_TASK_NOT_FOUND = "Task not found."
MSG_USER_NOT_FOUND = "User not found."
MSG_WORKSPACE_NOT_FOUND = "Workspace not found."
MSG_WORKSPACE_MEMBER_NOT_FOUND = "Workspace member not found."
MSG_PROJECT_NOT_FOUND = "Project not found."

MSG_FIELD_CANNOT_BE_NULL = "Field '{field_name}' cannot be null if provided."
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

# Workspace & Project messages
MSG_WORKSPACE_FORBIDDEN = "You do not have permission to perform this action."
MSG_WORKSPACE_MEMBER_ALREADY_EXISTS = "User is already a member of this workspace."
MSG_CANNOT_REMOVE_WORKSPACE_OWNER = "Cannot remove the workspace owner."
MSG_CANNOT_MODIFY_OWNER_ROLE = "Cannot change the workspace owner's role."
