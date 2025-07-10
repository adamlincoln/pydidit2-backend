# ruff: noqa: D105
"""Models for the initial database version."""

from datetime import datetime
from textwrap import shorten

from sqlalchemy import Column, ForeignKey, Table, Unicode, UnicodeText, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydiditbackend.models.base import Base
from pydiditbackend.models.enums import State
from pydiditbackend.models.util import get_new_lowest_display_position

todo_note = Table(
    "todo_note",
    Base.metadata,
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
    Column("note_id", ForeignKey("note.id"), primary_key=True),
)

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
    notes: Mapped[list["Note"]] = relationship(
        secondary=todo_note,
    )

    def __repr__(self) -> str:
        return f'<Todo id={self.id} display_position={self.display_position} {shorten(self.description, 20, placeholder="...")}>'  # noqa: E501

class Note(Base):
    """The Note model."""

    __tablename__ = "note"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    text: Mapped[str] = mapped_column(UnicodeText())
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f'<Note id={self.id} "{shorten(self.text, 20, placeholder="...")}">'

class Tag(Base):
    """The Tag model."""

    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(255))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )
