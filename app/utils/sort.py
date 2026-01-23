"""
Reusable sorting utility for SQLAlchemy queries.

Usage:
    from app.utils.sort import apply_sorting

    query = apply_sorting(
        query=query,
        model=Donor,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=['name', 'donor_code', 'created_at'],
        default_field='name'
    )
"""

from sqlalchemy import asc, desc
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select


def apply_sorting(
    query: Select,
    model: type[DeclarativeBase],
    sort_by: str | None = None,
    sort_order: str | None = None,
    allowed_fields: list[str] | None = None,
    default_field: str = 'created_at',
    default_order: str = 'desc'
) -> Select:
    """
    Apply sorting to a SQLAlchemy select query.
    
    Args:
        query: The SQLAlchemy Select query to sort
        model: The SQLAlchemy model class
        sort_by: Field name to sort by (must be in allowed_fields)
        sort_order: 'asc' or 'desc'
        allowed_fields: List of field names that can be sorted on (for security)
        default_field: Field to sort by if sort_by is not provided or invalid
        default_order: Sort order if not provided ('asc' or 'desc')
    
    Returns:
        The query with ORDER BY applied
    """
    # Validate sort_order
    order = sort_order.lower() if sort_order else default_order
    if order not in ('asc', 'desc'):
        order = default_order
    
    # Validate sort_by against allowed fields
    field = sort_by if sort_by else default_field
    if allowed_fields and field not in allowed_fields:
        field = default_field
    
    # Check if the field exists on the model
    if not hasattr(model, field):
        field = default_field
    
    # Get the column and apply ordering
    column = getattr(model, field)
    if order == 'desc':
        query = query.order_by(desc(column))
    else:
        query = query.order_by(asc(column))
    
    return query

