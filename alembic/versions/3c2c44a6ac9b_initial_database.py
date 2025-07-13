# ruff: noqa: INP001
"""
Initial database.

Revision ID: 3c2c44a6ac9b
Revises:
Create Date: 2025-07-07 23:37:15.821151

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from pydiditbackend.models.enums import State

# revision identifiers, used by Alembic.
revision: str = "3c2c44a6ac9b"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "todo",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("description", sa.Unicode(length=255), nullable=False),
        sa.Column(
            "state",
            sa.Enum(State, name="stateenum"),
            nullable=False,
        ),
        sa.Column("due", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.Column("show_from", sa.DateTime(), nullable=True),
        sa.Column("display_position", sa.BigInteger(), nullable=False, unique=True),
    )
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("description", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "state",
            sa.Enum(State, name="stateenum"),
            nullable=False,
        ),
        sa.Column("due", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.Column("show_from", sa.DateTime(), nullable=True),
        sa.Column("display_position", sa.BigInteger(), nullable=False, unique=True),
    )

    op.create_table(
        "project_contain_project",
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "child_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("parent_id", "child_id"),
    )

    op.create_table(
        "project_contain_todo",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id", "todo_id"),
    )

    op.create_table(
        "project_prereq_project",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "prereq_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id", "prereq_id"),
    )

    op.create_table(
        "project_prereq_todo",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id", "todo_id"),
    )

    op.create_table(
        "todo_prereq_project",
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("todo_id", "project_id"),
    )

    op.create_table(
        "todo_prereq_todo",
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.Column(
            "prereq_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("todo_id", "prereq_id"),
    )

    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("text", sa.UnicodeText(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("modified_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "project_note",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("note.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id", "note_id"),
    )

    op.create_table(
        "todo_note",
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("note.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("todo_id", "note_id"),
    )

    op.create_table(
        "project_tag",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tag.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("project_id", "tag_id"),
    )

    op.create_table(
        "todo_tag",
        sa.Column(
            "todo_id",
            sa.Integer(),
            sa.ForeignKey("todo.id"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tag.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("todo_id", "tag_id"),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("todo")
    op.drop_table("project")
    op.drop_table("project_contain_project")
    op.drop_table("project_contain_todo")
    op.drop_table("todo_prereq_todo")
    op.drop_table("todo_prereq_project")
    op.drop_table("project_prereq_project")
    op.drop_table("project_prereq_todo")
    op.drop_table("note")
    op.drop_table("tag")
    op.drop_table("todo_note")
    op.drop_table("project_note")
    op.drop_table("todo_tag")
    op.drop_table("project_tag")
