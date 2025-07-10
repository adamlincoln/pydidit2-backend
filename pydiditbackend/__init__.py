"""The primary API for pydiditbackend."""

import os

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

def get(model: str) -> models.Base:
    """Get instances."""
    with sessionmaker() as session:  # noqa: F821
        return session.scalars(select(getattr(models, model))).one()

def put(model: models.Base) -> models.Base:
    """Put an instance."""
    with sessionmaker() as session, session.begin():  # noqa: F821
        session.add(model)
    return model

if __name__ == "__main__":
    prepare(sqlalchemy_sessionmaker(create_engine(os.environ["DB_URL"])))
    #print(get("Todo"))
    put(models.Todo(  # type: ignore[attr-defined]
        description="fake",
        state=models.enums.State.active,
    ))
