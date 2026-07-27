from datetime import date

import pytest

from app.models.program import ProgramState
from app.services.errors import ConflictError, ValidationError
from app.services.program_service import ProgramService


@pytest.fixture
def service():
    return ProgramService()


def _valid_data(**overrides):
    data = {
        "name": "Spring Season",
        "description": "A season of films",
        "startDate": "2026-01-01",
        "endDate": "2026-06-30",
    }
    data.update(overrides)
    return data


def test_create_program_sets_defaults_and_creator_as_programmer(db, user_factory, service):
    creator = user_factory(username="creator")

    program = service.create_program(_valid_data(), creator)

    assert program.id is not None
    assert program.creation_date is not None
    assert program.state == ProgramState.CREATED
    assert program.name == "Spring Season"
    assert program.start_date == date(2026, 1, 1)
    assert program.end_date == date(2026, 6, 30)
    assert program.programmers == [creator]
    assert program.staff == []


@pytest.mark.parametrize("missing_field", ["name", "description", "startDate", "endDate"])
def test_create_program_missing_required_field(db, user_factory, service, missing_field):
    creator = user_factory()

    with pytest.raises(ValidationError):
        service.create_program(_valid_data(**{missing_field: ""}), creator)


def test_create_program_duplicate_name(db, user_factory, service):
    creator = user_factory()
    service.create_program(_valid_data(), creator)

    with pytest.raises(ConflictError):
        service.create_program(_valid_data(), creator)
