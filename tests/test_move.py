import os
from itertools import chain

import pydiditbackend
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker

@pytest.fixture
def prepare():
    engine = create_engine("sqlite:///:memory:", echo=True)
    pydiditbackend.prepare(sqlalchemy_sessionmaker(engine), version_override="3c2c44a6ac9b")
    pydiditbackend.models.base.Base.metadata.create_all(engine)
    yield
    engine.dispose()


def test_special_boundary_start_end(prepare):
    todos = (
        pydiditbackend.models.Todo(
            description=f"todo{i}",
            display_position=i,
        ) for i in range(10)
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]
    pydiditbackend.move(to_move, "end")

    pydiditbackend.get("Todo", filter_by={"description": "todo1"})[0].display_position == 10

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo7"},
    )[0]
    pydiditbackend.move(to_move, "start")

    pydiditbackend.get("Todo", filter_by={"description": "todo7"})[0].display_position == -1

def test_move_to_end_by_number(prepare):
    todos = (
        pydiditbackend.models.Todo(
            description=f"todo{i}",
            display_position=i,
        ) for i in range(10)
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]
    pydiditbackend.move(to_move, 9)

    pydiditbackend.get("Todo", filter_by={"description": "todo1"})[0].display_position == 10

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo7"},
    )[0]
    pydiditbackend.move(to_move, 0)

    pydiditbackend.get("Todo", filter_by={"description": "todo7"})[0].display_position == -1

def test_move_same_display_position(mocker, prepare):
    todos = (
        pydiditbackend.models.Todo(
            description=f"todo{i}",
            display_position=i,
        ) for i in range(10)
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]

    pydiditbackend.move(to_move, 1)

    pydiditbackend.get("Todo", filter_by={"description": "todo1"})[0].display_position == 1

def test_move_empty_spot(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(10)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(11, 21)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]

    pydiditbackend.move(to_move, 10)

    pydiditbackend.get("Todo", filter_by={"description": "todo1"})[0].display_position == 10

def test_move_occupied_spot_but_space_between(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(10)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(11, 21)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]

    pydiditbackend.move(to_move, 9)

    assert pydiditbackend.get("Todo", filter_by={"description": "todo1"})[0].display_position == 10

def test_move_occupied_spot_toward_end_one_move(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(1, 11)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(12, 22)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]

    pydiditbackend.move(to_move, 12)

    with pydiditbackend.sessionmaker() as session, session.begin():
        assert pydiditbackend.get("Todo", filter_by={"description": "todo10"}, session=session)[0].display_position == 10
        # there is no todo11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo12"}, session=session)[0].display_position == 11

        # this is what we just moved
        assert pydiditbackend.get("Todo", filter_by={"description": "todo1"}, session=session)[0].display_position == 12

        assert pydiditbackend.get("Todo", filter_by={"description": "todo13"}, session=session)[0].display_position == 13
        assert pydiditbackend.get("Todo", filter_by={"description": "todo14"}, session=session)[0].display_position == 14

def test_move_occupied_spot_toward_end_many_moves(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(1, 11)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(12, 22)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo1"},
    )[0]

    pydiditbackend.move(to_move, 18)

    with pydiditbackend.sessionmaker() as session, session.begin():
        assert pydiditbackend.get("Todo", filter_by={"description": "todo10"}, session=session)[0].display_position == 10
        # there is no todo11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo12"}, session=session)[0].display_position == 11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo13"}, session=session)[0].display_position == 12
        assert pydiditbackend.get("Todo", filter_by={"description": "todo14"}, session=session)[0].display_position == 13
        assert pydiditbackend.get("Todo", filter_by={"description": "todo15"}, session=session)[0].display_position == 14
        assert pydiditbackend.get("Todo", filter_by={"description": "todo16"}, session=session)[0].display_position == 15
        assert pydiditbackend.get("Todo", filter_by={"description": "todo17"}, session=session)[0].display_position == 16
        assert pydiditbackend.get("Todo", filter_by={"description": "todo18"}, session=session)[0].display_position == 17

        # this is what we just moved
        assert pydiditbackend.get("Todo", filter_by={"description": "todo1"}, session=session)[0].display_position == 18

        assert pydiditbackend.get("Todo", filter_by={"description": "todo19"}, session=session)[0].display_position == 19
        assert pydiditbackend.get("Todo", filter_by={"description": "todo20"}, session=session)[0].display_position == 20

def test_move_occupied_spot_toward_start_one_move(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(1, 11)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(12, 22)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo17"},
    )[0]

    pydiditbackend.move(to_move, 10)

    with pydiditbackend.sessionmaker() as session, session.begin():
        assert pydiditbackend.get("Todo", filter_by={"description": "todo12"}, session=session)[0].display_position == 12
        # there is no todo11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo10"}, session=session)[0].display_position == 11

        # this is what we just moved
        assert pydiditbackend.get("Todo", filter_by={"description": "todo17"}, session=session)[0].display_position == 10

        assert pydiditbackend.get("Todo", filter_by={"description": "todo9"}, session=session)[0].display_position == 9
        assert pydiditbackend.get("Todo", filter_by={"description": "todo8"}, session=session)[0].display_position == 8


def test_move_occupied_spot_toward_start_many_moves(mocker, prepare):
    todos = chain(
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(1, 11)
        ),
        (
            pydiditbackend.models.Todo(
                description=f"todo{i}",
                display_position=i,
            ) for i in range(12, 22)
        ),
    )

    with pydiditbackend.sessionmaker() as session, session.begin():
        for todo in todos:
            pydiditbackend.put(todo, session=session)

    to_move = pydiditbackend.get(
        "Todo",
        filter_by={"description": "todo17"},
    )[0]

    pydiditbackend.move(to_move, 4)

    with pydiditbackend.sessionmaker() as session, session.begin():
        assert pydiditbackend.get("Todo", filter_by={"description": "todo12"}, session=session)[0].display_position == 12
        # there is no todo11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo10"}, session=session)[0].display_position == 11
        assert pydiditbackend.get("Todo", filter_by={"description": "todo9"}, session=session)[0].display_position == 10
        assert pydiditbackend.get("Todo", filter_by={"description": "todo8"}, session=session)[0].display_position == 9
        assert pydiditbackend.get("Todo", filter_by={"description": "todo7"}, session=session)[0].display_position == 8
        assert pydiditbackend.get("Todo", filter_by={"description": "todo6"}, session=session)[0].display_position == 7
        assert pydiditbackend.get("Todo", filter_by={"description": "todo5"}, session=session)[0].display_position == 6
        assert pydiditbackend.get("Todo", filter_by={"description": "todo4"}, session=session)[0].display_position == 5

        # this is what we just moved
        assert pydiditbackend.get("Todo", filter_by={"description": "todo17"}, session=session)[0].display_position == 4

        assert pydiditbackend.get("Todo", filter_by={"description": "todo3"}, session=session)[0].display_position == 3
        assert pydiditbackend.get("Todo", filter_by={"description": "todo2"}, session=session)[0].display_position == 2
