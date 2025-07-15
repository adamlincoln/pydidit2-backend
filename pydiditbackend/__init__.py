# ruff: noqa: FIX002, T201, ERA001, TD002, TD003, TD004, TD006, RUF100
"""The primary API for pydiditbackend."""

import os
from collections.abc import Callable, Iterable
from datetime import datetime
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker
from sqlalchemy.sql.expression import ColumnElement

from pydiditbackend import models

sessionmaker: sqlalchemy_sessionmaker

P = ParamSpec("P")  # Represents the parameters of the decorated function
R = TypeVar("R")    # Represents the return type of the decorated function

def handle_session(*args, expunge: bool = False):
    def handle_session_inside(f: Callable[P, R]) -> Callable[P, R]:
        @wraps(f)
        def wrapper(*inside_args, **inside_kwargs):
            if (session := inside_kwargs.get("session")) is None:
                with sessionmaker() as session, session.begin():  # noqa: F821, PLR1704
                    inside_kwargs["session"] = session
                    to_return = f(*inside_args, **inside_kwargs)
                    if expunge:
                        session.expunge_all()
                    return to_return
            else:
                return f(*inside_args, **inside_kwargs)
        return wrapper
    if len(args) > 0 and callable(args[0]):
        return handle_session_inside(args[0])
    else:
        return handle_session_inside

def prepare(provided_sessionmaker: sqlalchemy_sessionmaker) -> None:
    """
    Prepare the backend.

    This must be called before using any of the other functions.
    """
    globals()["sessionmaker"] = provided_sessionmaker
    models.prepare(provided_sessionmaker)

@overload
def get(
    model: str,
    *,
    filter=None,
    filter_by: dict[str, int | str] | None = None,
    include_completed: bool = False,
    session: sqlalchemy_sessionmaker | None = None,
    where: ColumnElement[bool] | None = None,
) -> Iterable[models.Base]:
    ...

@overload
def get(
    model: models.Base,
    *,
    filter=None,
    filter_by: dict[str, int | str] | None = None,
    include_completed: bool = False,
    session: sqlalchemy_sessionmaker | None = None,
    where: ColumnElement[bool] | None = None,
) -> Iterable[models.Base]:
    ...

@handle_session(expunge=True)
def get(
    model,
    *,
    filter=None,
    filter_by=None,
    include_completed=False,
    session=None,
    where=None,
):
    """Get instances."""
    model = getattr(models, model) if isinstance(model, str) else model
    query = select(model)
    if filter is not None:
        query = query.filter(filter)
    if filter_by is not None:
        query = query.filter_by(**filter_by)
    if not include_completed and hasattr(model, "state"):
        query = query.filter_by(state=models.enums.State.active)
    if where is not None:
        query = query.where(where)
    if hasattr(model, "display_position"):
        query = query.order_by(model.display_position)

    return session.scalars(query).unique().all()  # type: ignore[attr-defined]

@handle_session
def put(
    instance: models.Base,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> models.Base:
    """Put an instance."""
    session.add(instance)  # type: ignore[attr-defined]
    return instance

@overload
def delete(
    instance: models.Base,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> None:
    ...

@overload
def delete(
    model_name: str,
    instance_id: int,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> None:
    ...

@handle_session
def delete(
    *args,
    **kwargs,
) -> None:
    """Delete an instance."""
    session = kwargs.get("session")
    if len(args) == 1:
        instance = args[0]
    else:
        instance = get(
            args[0],
            filter_by={"id": args[1]},
            session=session,
        )[0]
    session.delete(instance)  # type: ignore[attr-defined]

@overload
def mark_completed(
    instance: models.Base,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> None:
    ...

@overload
def mark_completed(
    model_name: str,
    instance_id: int,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> None:
    ...

@handle_session
def mark_completed(
    *args,
    **kwargs,
) -> None:
    """Mark an instance as completed."""
    if len(args) == 1:
        instance = args[0]
    else:
        session = kwargs.get("session")
        instance = get(
            args[0],
            filter_by={"id": args[1]},
            session=session,
        )[0]
    instance.state = models.enums.State.completed

"""
if __name__ == "__main__":
    prepare(sqlalchemy_sessionmaker(create_engine(os.environ["PYDIDIT_DB_URL"])))

    project_description = "test project"
    put(models.Project(description=project_description, state=models.enums.State.active))
    project = get("Project", filter_by={"description": project_description})[0]
    with sessionmaker() as session, session.begin():
        display_position = models.util.get_new_lowest_display_position(models.Todo.display_position)
        for i in range(10):
            todo = models.Todo(description=f"test project todo {i}", display_position=display_position + i)
            todo.contained_by_projects.append(project)
            put(todo, session=session)
    print(get("Project", filter_by={"description": project_description})[0])
    print(get("Project", filter_by={"description": project_description})[0].contain_todos)

    print(get(models.Todo))
    tag_name = "for testing"
    put(models.Tag(name=tag_name))
    with sessionmaker() as session, session.begin():
        new_todo = models.Todo(  # type: ignore[attr-defined]
            description="testing delete",
            state=models.enums.State.active,
        )
        new_todo.tags.append(get("Tag", filter_by={"name": tag_name}, session=session)[0])
        put(new_todo, session=session)
    print(get(models.Todo))
    delete(get("Todo", where=models.Todo.tags.any(models.Tag.name == tag_name))[0])
    print(get(models.Todo))
    delete(get(models.Tag, filter_by={"name": tag_name})[0])

    with sessionmaker() as session, session.begin():  # noqa: F821
        print(get(models.Todo, session=session))
        new_todo = models.Todo(  # type: ignore[attr-defined]
            description="testing delete",
            state=models.enums.State.active,
        )
        put(new_todo, session=session)
        print(new_todo)
        print(get(models.Todo, session=session))
        delete(new_todo, session=session)
        print(get(models.Todo, session=session))

    put(models.Todo(  # type: ignore[attr-defined]
        description="fake show from",
        state=models.enums.State.active,
        show_from=datetime.fromisoformat("2025-12-01T10:00:00Z"),
        due=datetime.fromisoformat("2025-12-02T11:00:00Z"),
    ))
    print(get(models.Todo))
    print([todo.due for todo in get(models.Todo)])

    with sessionmaker() as session:  # noqa: F821
        print(get(models.Project, session=session)[0].contain_projects)  # type: ignore[attr-defined, index]
        print(get(models.Project, session=session)[0].contained_by_projects)  # type: ignore[attr-defined, index]
    with sessionmaker() as session:  # noqa: F821
        print(get(models.Project, session=session)[0].contain_todos)  # type: ignore[attr-defined, index]
        print(get(models.Todo, session=session)[0].contained_by_projects)  # type: ignore[attr-defined, index]
    with sessionmaker() as session:  # noqa: F821
        print(get(models.Todo, session=session))  # type: ignore[attr-defined]
        print([
            (todo, todo.notes)  # type: ignore[attr-defined]
            for todo
            in get(models.Todo, session=session)  # type: ignore[attr-defined]
        ])
        print([
            (todo, todo.prereq_todos)  # type: ignore[attr-defined]
            for todo
            in get(models.Todo, session=session)  # type: ignore[attr-defined]
        ])
        print([
            (todo, todo.dependent_todos)  # type: ignore[attr-defined]
            for todo
            in get(models.Todo, session=session)  # type: ignore[attr-defined]
        ])
    print(get(models.Todo))
    print(get(models.Project))
    with sessionmaker() as session:
        print(get(models.Project, session=session)[0].dependent_todos)
        print(get(models.Todo, session=session)[0].prereq_projects)
    with sessionmaker() as session:  # noqa: F821
        print(get(models.Project, session=session)[0].prereq_todos)  # type: ignore[attr-defined, index]
        print(get(models.Todo, session=session)[0].dependent_projects)  # type: ignore[attr-defined, index]
    print(get(models.Tag))
    put(models.Todo(  # type: ignore[attr-defined]
        description="fake",
        state=models.enums.State.active,
    ))
    put(models.Project(  # type: ignore[attr-defined]
        description="fakeproject1",
        state=models.enums.State.active,
    ))
    note = put(models.Note(  # type: ignore[attr-defined]
        text="This is an awesome note 2",
    ))
    with sessionmaker() as session, session.begin():  # noqa: F821
        note = put(
            models.Note(  # type: ignore[attr-defined]
                text="This is an awesome note 3",
            ),
            session=session,
        )
        todo = get(
            models.Todo,
            session=session,
        )[0]
        todo.notes.append(note)
"""
