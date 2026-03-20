from typing import Set


def validate_sort_field(sort: str, allowed_fields: Set[str], default: str = "id") -> str:
    """Validate that the sort field is in the allowed set. Returns default if not allowed."""
    if sort in allowed_fields:
        return sort
    return default
