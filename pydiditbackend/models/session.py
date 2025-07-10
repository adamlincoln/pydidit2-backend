"""A module for accessing the sessionmaker."""

from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker


def prepare_sessionmaker(sessionmaker: sqlalchemy_sessionmaker) -> None:
    """Prepare the globally importable sessionmaker."""
    globals()["sessionmaker"] = sessionmaker
