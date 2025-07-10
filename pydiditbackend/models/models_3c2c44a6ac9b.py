"""Models for the initial database version."""

from datetime import datetime

from sqlalchemy import Unicode, func
from sqlalchemy.orm import Mapped, mapped_column

from pydiditbackend.models.base import Base
from pydiditbackend.models.enums import State
from pydiditbackend.models.util import get_new_lowest_display_position


class Todo(Base):
    """The Todo model."""

    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    description: Mapped[str] = mapped_column(Unicode(255))
    state: Mapped[State]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )
    display_position: Mapped[int] = mapped_column(
        default=get_new_lowest_display_position,
    )

