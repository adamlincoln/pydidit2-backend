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

todo_tag = Table(
    "todo_tag",
    Base.metadata,
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)

project_note = Table(
    "project_note",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("note_id", ForeignKey("note.id"), primary_key=True),
)

project_tag = Table(
    "project_tag",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)

todo_prereq_todo = Table(
    "todo_prereq_todo",
    Base.metadata,
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
    Column("prereq_id", ForeignKey("todo.id"), primary_key=True),
)

project_prereq_project = Table(
    "project_prereq_project",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("prereq_id", ForeignKey("project.id"), primary_key=True),
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
    prereq_todos: Mapped[list["Todo"]] = relationship(
        secondary=todo_prereq_todo,
        back_populates="dependent_todos",
        primaryjoin=id == todo_prereq_todo.c.todo_id,
        secondaryjoin=id == todo_prereq_todo.c.prereq_id,
    )
    dependent_todos: Mapped[list["Todo"]] = relationship(
        secondary=todo_prereq_todo,
        back_populates="prereq_todos",
        primaryjoin=id == todo_prereq_todo.c.prereq_id,
        secondaryjoin=id == todo_prereq_todo.c.todo_id,
    )
    notes: Mapped[list["Note"]] = relationship(
        secondary=todo_note,
        back_populates="todos",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=todo_tag,
        back_populates="todos",
    )

    def __repr__(self) -> str:
        return f'<Todo id={self.id} display_position={self.display_position} {shorten(self.description, 20, placeholder="...")}>'  # noqa: E501

class Project(Base):
    """The Project model."""

    __tablename__ = "project"

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
    prereq_projects: Mapped[list["Project"]] = relationship(
        secondary=project_prereq_project,
        back_populates="dependent_projects",
        primaryjoin=id == project_prereq_project.c.project_id,
        secondaryjoin=id == project_prereq_project.c.prereq_id,
    )
    dependent_projects: Mapped[list["Project"]] = relationship(
        secondary=project_prereq_project,
        back_populates="prereq_projects",
        primaryjoin=id == project_prereq_project.c.prereq_id,
        secondaryjoin=id == project_prereq_project.c.project_id,
    )
    notes: Mapped[list["Note"]] = relationship(
        secondary=project_note,
        back_populates="projects",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=project_tag,
        back_populates="projects",
    )

    def __repr__(self) -> str:
        return f'<Project id={self.id} display_position={self.display_position} {shorten(self.description, 20, placeholder="...")}>'  # noqa: E501

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
    todos: Mapped[list[Todo]] = relationship(
        secondary=todo_note,
        back_populates="notes",
    )
    projects: Mapped[list[Project]] = relationship(
        secondary=project_note,
        back_populates="notes",
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
    todos: Mapped[list[Todo]] = relationship(
        secondary=todo_tag,
        back_populates="tags",
    )
    projects: Mapped[list[Project]] = relationship(
        secondary=project_tag,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f'<Tag id={self.id} "{shorten(self.name, 20, placeholder="...")}">'
