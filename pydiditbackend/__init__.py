# ruff: noqa: FIX002, T201, ERA001, TD002, TD003, TD004, TD006, RUF100
"""The primary API for pydiditbackend."""

import os
from collections.abc import Callable, Iterable
from datetime import datetime
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from sqlalchemy import and_, create_engine, desc, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker
from sqlalchemy.sql.expression import ColumnElement

from pydiditbackend import models

sessionmaker: sqlalchemy_sessionmaker

P = ParamSpec("P")  # Represents the parameters of the decorated function
R = TypeVar("R")    # Represents the return type of the decorated function

MOVE_OFFSET = 1000000000

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

def prepare(
    provided_sessionmaker: sqlalchemy_sessionmaker,
    *,
    version_override=None,
) -> None:
    """
    Prepare the backend.

    This must be called before using any of the other functions.
    """
    globals()["sessionmaker"] = provided_sessionmaker
    models.prepare(provided_sessionmaker, version_override=version_override)

@overload
def get(
    model: str,
    *,
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
    filter_by=None,
    include_completed=False,
    include_future_show_from=False,
    session=None,
    where=None,
):
    """Get instances."""
    model = getattr(models, model) if isinstance(model, str) else model
    query = select(model)
    if filter_by is not None:
        query = query.filter_by(**filter_by)
    if not include_completed and hasattr(model, "state"):
        query = query.filter_by(state=models.enums.State.active)
    if not include_future_show_from and hasattr(model, "show_from"):
        query = query.where(or_(
            model.show_from is None,
            model.show_from <= datetime.now(),
        ))
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
            include_completed=True,
            include_future_show_from=True,
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
            include_future_show_from=True,
        )[0]
    instance.state = models.enums.State.completed

def _move_to_boundary(
    instance: models.Base,
    session,
    *,
    start: bool = True,
) -> None:
    display_position_column = getattr(
        type(instance),
        "display_position",
    )

    query = select(display_position_column).limit(1)

    if start:
        query = query.order_by(display_position_column)
    else:
        query = query.order_by(desc(display_position_column))
    boundary_display_position = session.scalars(query).one()
    instance.display_position = (
        boundary_display_position - 1
        if start
        else boundary_display_position + 1
    )


def move(
    *args,
) -> None:
    """Move an instance to a new display position. Unlike other backend function, this cannot be called with an existing session."""
    fix_offsets = False
    with sessionmaker() as session, session.begin():
        if len(args) < 2:
            raise ValueError(
                f"You must provide at least two args."
            )
        if len(args) == 2:
            instance = args[0]
            instance = session.merge(instance)
        else:
            try:
                instance = session.scalars(
                    select(getattr(models, args[0])).filter_by(id=args[1])
                ).unique().one()
            except NoResultFound:
                raise ValueError(
                    f"There must be exactly one {args[0]} to move."
                )

        instance_id = instance.id

        if isinstance(args[-1], models.Base):
            new_display_position = args[-1].display_position
        else:
            new_display_position = args[-1]

        # special cases
        if new_display_position == "start" or new_display_position == "end":
            _move_to_boundary(instance, session, start=(new_display_position == "start"))
            return

        new_display_position = int(new_display_position)

        # no real change
        if instance.display_position == new_display_position:
            return

        display_position_column = getattr(
            type(instance),
            "display_position",
        )

        # look for empty spot
        try:
            blocking_instance = session.scalars(
                select(type(instance)).filter_by(
                    display_position=new_display_position,
                )
            ).unique().one()
        except NoResultFound:
            instance.display_position = new_display_position
            return
        blocking_instance_id = blocking_instance.id

        toward_start = instance.display_position > new_display_position

        try:
            next_instance = session.scalars(
                select(type(instance)).where(
                    display_position_column < new_display_position
                    if toward_start
                    else display_position_column > new_display_position
                ).order_by(
                    desc(display_position_column) if toward_start else display_position_column
                ).limit(1)).unique().one()
        except NoResultFound:
            # we asked for the start or the end
            instance.display_position = (
                new_display_position - 1
                if toward_start
                else new_display_position + 1
            )
        else:
            if abs(new_display_position - next_instance.display_position) > 1:
                # there's room in between the requested position and the next position, so use it
                instance.display_position = (
                    new_display_position - 1
                    if toward_start
                    else new_display_position + 1
                )
            else:
                # we need to move stuff to make room

                # This is the logic if we are moving toward the start:
                # Find highest empty display position between the input instance and new_display_position
                # (which is occupied by blocking_instance), not inclusive of these endpoints.
                # If there are none, then the *low* limit of the range we need to move is the
                # input instance (except that we will be moving the input instance, so we really need to stop
                # moving at the one next to the input instance, on the high side).  If there is one, then the
                # low limit of the range we need to move is the one next to the empty display position, on the
                # high side.  The high limit of the range we need to move is blocking_instance.  All within the
                # range are moved one display position *lower*.  Then the input instance is assigned new_display_position.

                # The logic for moving toward the end is reserved.

                fix_offsets = True
                updated_instance_ids = set()

                in_between_query_range = and_(
                    display_position_column > blocking_instance.display_position,
                    display_position_column < instance.display_position,
                ) if toward_start else and_(
                    display_position_column < blocking_instance.display_position,
                    display_position_column > instance.display_position,
                )

                in_between_order_by = display_position_column if toward_start else desc(display_position_column)

                in_between_instances = session.scalars(
                    select(type(instance)).where(in_between_query_range).order_by(in_between_order_by)
                ).unique().all()

                display_position_range = range(
                    blocking_instance.display_position + (1 if toward_start else -1),
                    instance.display_position,
                    1 if toward_start else -1,
                )

                for in_between_instance, display_position in zip(
                    in_between_instances,
                    display_position_range,
                ):
                    if in_between_instance.display_position == display_position:
                        in_between_instance.display_position += (1 if toward_start else -1) + MOVE_OFFSET
                        updated_instance_ids.add(in_between_instance.id)
                    else:
                        break

                blocking_instance.display_position += (1 if toward_start else -1) + MOVE_OFFSET
                instance.display_position = new_display_position + MOVE_OFFSET

    # We have to play this offset game because sqlite, a DB we want to
    # support, does not offer deferred unique constraints.
    if fix_offsets:
        with sessionmaker() as session, session.begin():
            updated_instances = session.scalars(select(type(instance)).where(
                type(instance).id.in_(updated_instance_ids)
            )).unique().all()
            for updated_instance in updated_instances:
                updated_instance.display_position -= MOVE_OFFSET
            if blocking_instance_id is not None:
                blocking_instance = session.scalars(select(type(instance)).filter_by(
                    id=blocking_instance_id,
                )).unique().one()
                blocking_instance.display_position -= MOVE_OFFSET

            instance = session.scalars(select(type(instance)).filter_by(
                id=instance_id,
            )).unique().one()
            instance.display_position -= MOVE_OFFSET

@handle_session(expunge=True)
def search(
    *args,
    **kwargs,
) -> list[models.Base]:
    """Search all models by primary descriptor."""
    # TODO (alincoln) add switches to include completed or future show from
    session = kwargs.get("session")
    instances = []
    for model_name in ("Todo", "Project", "Tag", "Note"):
        model = getattr(models, model_name)
        instances.extend(get(
            model_name,
            where=getattr(
                model,
                model.primary_descriptor,
            ).ilike(f"%{args[0]}%"),
            session=session,
        ))
    return instances

"""
if __name__ == "__main__":
    prepare(sqlalchemy_sessionmaker(create_engine(os.environ["PYDIDIT_DB_URL"])))

    print(get("Todo"))
    print(get("Project"))
    print(search("test"))

    put(models.Todo(
        description="fake show from 1234",
        state=models.enums.State.active,
        show_from=datetime.fromisoformat("2026-12-01T10:00:00Z"),
        due=datetime.fromisoformat("2025-12-02T11:00:00Z"),
    ))
    the_todos = get("Todo", filter_by={"description":"fake show from 1234"}, include_future_show_from=True)
    print(the_todos)
    for el in the_todos:
        delete("Todo", el.id)

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
