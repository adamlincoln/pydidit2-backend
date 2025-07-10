# ruff: noqa: FIX002, T201, ERA001, TD002, TD003, TD004, TD006, RUF100
"""The primary API for pydiditbackend."""

import os
from collections.abc import Iterable
from typing import overload

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker

from pydiditbackend import models

sessionmaker: sqlalchemy_sessionmaker

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
    session: sqlalchemy_sessionmaker | None = None,
) -> Iterable[models.Base]:
    ...

@overload
def get(
    model: models.Base,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> Iterable[models.Base]:
    ...

def get(model, *, session=None):
    """Get instances."""
    model = getattr(models, model) if isinstance(model, str) else model
    query = select(model)
    if hasattr(model, "display_position"):
        query = query.order_by(model.display_position)

    def execute(session: sqlalchemy_sessionmaker) -> Iterable[models.Base]:
        return session.scalars(query).all()  # type: ignore[attr-defined]

    if session is None:
        with sessionmaker() as session:  # noqa: F821, PLR1704
            return execute(session)
    else:
        return execute(session)

def put(
    model: models.Base,
    *,
    session: sqlalchemy_sessionmaker | None = None,
) -> models.Base:
    """Put an instance."""
    def execute(session: sqlalchemy_sessionmaker) -> models.Base:
        session.add(model)  # type: ignore[attr-defined]
        return model

    if session is None:
        with sessionmaker() as session, session.begin():  # noqa: F821, PLR1704
            return execute(session)
    else:
        return execute(session)

if __name__ == "__main__":
    prepare(sqlalchemy_sessionmaker(create_engine(os.environ["DB_URL"])))
    #with sessionmaker() as session:  # noqa: F821
        #print(get(models.Todo, session=session))  # type: ignore[attr-defined]
        #print([
            #(todo, todo.notes)  # type: ignore[attr-defined]
            #for todo
            #in get(models.Todo, session=session)  # type: ignore[attr-defined]
        #])
        #print([
            #(todo, todo.prereq_todos)  # type: ignore[attr-defined]
            #for todo
            #in get(models.Todo, session=session)  # type: ignore[attr-defined]
        #])
        #print([
            #(todo, todo.dependent_todos)  # type: ignore[attr-defined]
            #for todo
            #in get(models.Todo, session=session)  # type: ignore[attr-defined]
        #])
    #print(get(models.Todo))
    #print(get(models.Project))
    #print(get(models.Tag))
    #put(models.Todo(  # type: ignore[attr-defined]
        #description="fake",
        #state=models.enums.State.active,
    #))
    #put(models.Project(  # type: ignore[attr-defined]
        #description="fakeproject1",
        #state=models.enums.State.active,
    #))
    #note = put(models.Note(  # type: ignore[attr-defined]
        #text="This is an awesome note 2",
    #))
    #with sessionmaker() as session, session.begin():  # noqa: F821
        #note = put(
            #models.Note(  # type: ignore[attr-defined]
                #text="This is an awesome note 3",
            #),
            #session=session,
        #)
        #todo = get(
            #models.Todo,
            #session=session,
        #)[0]
        #todo.notes.append(note)
