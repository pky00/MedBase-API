"""
Request context utilities using starlette-context.

Provides access to current user and database session throughout the request lifecycle.
"""

from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError
from app.models.user import User


class ContextKeys:
    """Keys for context storage."""

    CURRENT_USER = "current_user"
    CURRENT_USERNAME = "current_username"


def set_current_user(user: User) -> None:
    """Store current user in request context."""
    context[ContextKeys.CURRENT_USER] = user
    context[ContextKeys.CURRENT_USERNAME] = user.username


def get_current_user_from_context() -> User | None:
    """Get current user from request context."""
    try:
        return context.get(ContextKeys.CURRENT_USER)
    except ContextDoesNotExistError:
        return None


def get_current_username() -> str | None:
    """Get current username from request context."""
    try:
        return context.get(ContextKeys.CURRENT_USERNAME)
    except ContextDoesNotExistError:
        return None


def get_audit_user() -> str:
    """
    Get username for audit fields (created_by, updated_by).
    Returns 'system' if no user in context.
    """
    username = get_current_username()
    return username if username else "system"

