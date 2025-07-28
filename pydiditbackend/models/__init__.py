"""Models."""

from importlib import import_module

from sqlalchemy import select
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy.orm import (
    sessionmaker as sqlalchemy_sessionmaker,
)

from pydiditbackend.models.base import Base
from pydiditbackend.models.session import prepare_sessionmaker


class AlembicVersion(Base):
    """The model for the alembic_version table."""

    __tablename__ = "alembic_version"

    version_num: Mapped[str] = mapped_column(primary_key=True)

def prepare(
    sessionmaker: sqlalchemy_sessionmaker,
    *,
    version_override=None,
) -> None:
    """Prepare the models."""
    prepare_sessionmaker(sessionmaker)
    if version_override is None:
        with sessionmaker() as session:
            version_num = session.execute(
                select(AlembicVersion.version_num),
            ).one().version_num
    else:
        version_num = version_override
    versioned_models = import_module(
        f"pydiditbackend.models.models_{version_num}",
    )
    for attribute_name in dir(versioned_models):
        attribute = getattr(versioned_models, attribute_name)
        try:
            if issubclass(attribute, Base):
                globals()[attribute_name] = attribute
        except TypeError:
            pass
