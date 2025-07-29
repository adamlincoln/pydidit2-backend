# ruff: noqa: D105
"""Models for the initial database version."""

from datetime import datetime
from textwrap import shorten

from sqlalchemy import Column, ForeignKey, Table, Unicode, UnicodeText, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydiditbackend.models.base import Base
from pydiditbackend.models.enums import State
from pydiditbackend.models.util import get_new_lowest_display_position_default

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

todo_prereq_project = Table(
    "todo_prereq_project",
    Base.metadata,
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
    Column("project_id", ForeignKey("project.id"), primary_key=True),
)

project_prereq_project = Table(
    "project_prereq_project",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("prereq_id", ForeignKey("project.id"), primary_key=True),
)

project_prereq_todo = Table(
    "project_prereq_todo",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
)

project_contain_project = Table(
    "project_contain_project",
    Base.metadata,
    Column("parent_id", ForeignKey("project.id"), primary_key=True),
    Column("child_id", ForeignKey("project.id"), primary_key=True),
)

project_contain_todo = Table(
    "project_contain_todo",
    Base.metadata,
    Column("project_id", ForeignKey("project.id"), primary_key=True),
    Column("todo_id", ForeignKey("todo.id"), primary_key=True),
)

class Todo(Base):
    """The Todo model."""

    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    description: Mapped[str] = mapped_column(Unicode(255))
    state: Mapped[State] = mapped_column(default=State.active)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )
    show_from: Mapped[datetime | None]
    due: Mapped[datetime | None]
    display_position: Mapped[int] = mapped_column(
        default=get_new_lowest_display_position_default,
        unique=True,
    )
    prereq_todos: Mapped[list["Todo"]] = relationship(
        secondary=todo_prereq_todo,
        back_populates="dependent_todos",
        primaryjoin=id == todo_prereq_todo.c.todo_id,
        secondaryjoin=id == todo_prereq_todo.c.prereq_id,
        lazy="joined",
    )
    prereq_projects: Mapped[list["Project"]] = relationship(
        secondary=todo_prereq_project,
        back_populates="dependent_todos",
        lazy="joined",
    )
    dependent_todos: Mapped[list["Todo"]] = relationship(
        secondary=todo_prereq_todo,
        back_populates="prereq_todos",
        primaryjoin=id == todo_prereq_todo.c.prereq_id,
        secondaryjoin=id == todo_prereq_todo.c.todo_id,
        lazy="joined",
    )
    dependent_projects: Mapped[list["Project"]] = relationship(
        secondary=project_prereq_todo,
        back_populates="prereq_todos",
        lazy="joined",
    )
    contained_by_projects: Mapped[list["Project"]] = relationship(
        secondary=project_contain_todo,
        back_populates="contain_todos",
        lazy="joined",
    )
    notes: Mapped[list["Note"]] = relationship(
        secondary=todo_note,
        back_populates="todos",
        lazy="joined",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=todo_tag,
        back_populates="todos",
        lazy="joined",
    )
    primary_descriptor: str = "description"

    def __repr__(self) -> str:
        return f'<Todo {shorten(self.description, 20, placeholder="...")} id={self.id} {self.state.value} display_position={self.display_position}>'  # noqa: E501

class Project(Base):
    """The Project model."""

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    description: Mapped[str] = mapped_column(Unicode(255))
    state: Mapped[State] = mapped_column(default=State.active)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )
    show_from: Mapped[datetime | None]
    due: Mapped[datetime | None]
    display_position: Mapped[int] = mapped_column(
        default=get_new_lowest_display_position_default,
        unique=True,
    )
    prereq_projects: Mapped[list["Project"]] = relationship(
        secondary=project_prereq_project,
        back_populates="dependent_projects",
        primaryjoin=id == project_prereq_project.c.project_id,
        secondaryjoin=id == project_prereq_project.c.prereq_id,
        lazy="joined",
    )
    dependent_projects: Mapped[list["Project"]] = relationship(
        secondary=project_prereq_project,
        back_populates="prereq_projects",
        primaryjoin=id == project_prereq_project.c.prereq_id,
        secondaryjoin=id == project_prereq_project.c.project_id,
        lazy="joined",
    )
    dependent_todos: Mapped[list[Todo]] = relationship(
        secondary=todo_prereq_project,
        back_populates="prereq_projects",
        lazy="joined",
    )
    prereq_todos: Mapped[list[Todo]] = relationship(
        secondary=project_prereq_todo,
        back_populates="dependent_projects",
        lazy="joined",
    )
    contain_todos: Mapped[list[Todo]] = relationship(
        secondary=project_contain_todo,
        back_populates="contained_by_projects",
        lazy="joined",
    )
    contain_projects: Mapped[list["Project"]] = relationship(
        secondary=project_contain_project,
        back_populates="contained_by_projects",
        primaryjoin=id == project_contain_project.c.parent_id,
        secondaryjoin=id == project_contain_project.c.child_id,
        lazy="joined",
    )
    contained_by_projects: Mapped[list["Project"]] = relationship(
        secondary=project_contain_project,
        back_populates="contain_projects",
        primaryjoin=id == project_contain_project.c.child_id,
        secondaryjoin=id == project_contain_project.c.parent_id,
        lazy="joined",
    )
    notes: Mapped[list["Note"]] = relationship(
        secondary=project_note,
        back_populates="projects",
        lazy="joined",
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=project_tag,
        back_populates="projects",
        lazy="joined",
    )
    primary_descriptor: str = "description"

    def __repr__(self) -> str:
        return f'<Project {shorten(self.description, 20, placeholder="...")} id={self.id} {self.state.value} display_position={self.display_position} {len(self.contain_todos)} todos>'  # noqa: E501

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
        lazy="joined",
    )
    projects: Mapped[list[Project]] = relationship(
        secondary=project_note,
        back_populates="notes",
        lazy="joined",
    )
    primary_descriptor: str = "text"

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
        lazy="joined",
    )
    projects: Mapped[list[Project]] = relationship(
        secondary=project_tag,
        back_populates="tags",
        lazy="joined",
    )
    primary_descriptor: str = "name"

    def __repr__(self) -> str:
        return f'<Tag {shorten(self.name, 20, placeholder="...")} id={self.id}>'
