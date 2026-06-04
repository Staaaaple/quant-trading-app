"""API dependencies."""

from fastapi import Header, HTTPException


def get_current_user_id(x_user_id: int | None = Header(None, alias="X-User-Id")) -> int | None:
    """从请求头获取当前用户 ID.

    前端通过 X-User-Id header 传递当前登录用户 ID，
    后端用这个 ID 来过滤数据，实现多用户隔离。
    """
    return x_user_id


def require_user_id(x_user_id: int | None = Header(None, alias="X-User-Id")) -> int:
    """要求必须提供用户 ID，否则返回 401."""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="User ID required. Please select a user.")
    return x_user_id
