"""Model utils."""

from sqlalchemy import desc, select

from pydiditbackend.models.session import sessionmaker  # type: ignore[attr-defined]


def get_new_lowest_display_position_default(context) -> int:  # noqa: ANN001
    """Get the new lowest display position for a default sqlalchemy value."""
    return get_new_lowest_display_position(context.current_column)

def get_new_lowest_display_position(column) -> int:
    """Get the new lowest display position."""
    with sessionmaker() as session:
        lowest_display_position = session.scalars(
            select(column).order_by(desc(column)),
        ).first()
    return 0 if lowest_display_position is None else lowest_display_position + 1
