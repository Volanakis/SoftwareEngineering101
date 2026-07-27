from datetime import date

import pytest

from app.models.program import ProgramState
from app.services.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
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


def test_update_program_applies_partial_changes(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    updated = service.update_program(
        program.id, {"description": "Updated description"}, creator
    )

    assert updated.description == "Updated description"
    assert updated.name == "Spring Season"


def test_update_program_rejects_non_programmer(db, user_factory, service):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(AuthorizationError):
        service.update_program(program.id, {"description": "Nope"}, outsider)


def test_update_program_rejects_when_announced(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)
    program.state = ProgramState.ANNOUNCED
    db.session.commit()

    with pytest.raises(ConflictError):
        service.update_program(program.id, {"description": "Nope"}, creator)


def test_update_program_rejects_empty_name(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(ValidationError):
        service.update_program(program.id, {"name": ""}, creator)


def test_update_program_rejects_duplicate_name(db, user_factory, service):
    creator = user_factory(username="creator")
    service.create_program(_valid_data(name="Autumn Season"), creator)
    program = service.create_program(_valid_data(name="Spring Season"), creator)

    with pytest.raises(ConflictError):
        service.update_program(program.id, {"name": "Autumn Season"}, creator)


def test_update_program_unknown_id_raises_not_found(db, user_factory, service):
    creator = user_factory(username="creator")

    with pytest.raises(NotFoundError):
        service.update_program("does-not-exist", {"description": "x"}, creator)


def test_add_programmer_success(db, user_factory, service):
    creator = user_factory(username="creator")
    new_programmer = user_factory(username="new-programmer")
    program = service.create_program(_valid_data(), creator)

    updated = service.add_programmer(program.id, new_programmer.id, creator)

    assert set(updated.programmers) == {creator, new_programmer}


def test_add_programmer_rejects_non_programmer_requester(db, user_factory, service):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    target = user_factory(username="target")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(AuthorizationError):
        service.add_programmer(program.id, target.id, outsider)


def test_add_programmer_rejects_user_already_programmer(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(ConflictError):
        service.add_programmer(program.id, creator.id, creator)


def test_add_programmer_rejects_user_already_staff(db, user_factory, service):
    creator = user_factory(username="creator")
    staff_member = user_factory(username="staffer")
    program = service.create_program(_valid_data(), creator)
    service.add_staff(program.id, staff_member.id, creator)

    with pytest.raises(ConflictError):
        service.add_programmer(program.id, staff_member.id, creator)


def test_add_programmer_rejects_when_announced(db, user_factory, service):
    creator = user_factory(username="creator")
    target = user_factory(username="target")
    program = service.create_program(_valid_data(), creator)
    program.state = ProgramState.ANNOUNCED
    db.session.commit()

    with pytest.raises(ConflictError):
        service.add_programmer(program.id, target.id, creator)


def test_add_programmer_unknown_program_raises_not_found(db, user_factory, service):
    creator = user_factory(username="creator")

    with pytest.raises(NotFoundError):
        service.add_programmer("does-not-exist", creator.id, creator)


def test_add_programmer_unknown_user_raises_not_found(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(NotFoundError):
        service.add_programmer(program.id, "does-not-exist", creator)


def test_add_staff_success_while_created(db, user_factory, service):
    creator = user_factory(username="creator")
    staff_member = user_factory(username="staffer")
    program = service.create_program(_valid_data(), creator)

    updated = service.add_staff(program.id, staff_member.id, creator)

    assert updated.staff == [staff_member]


def test_add_staff_rejects_once_program_left_created(db, user_factory, service):
    creator = user_factory(username="creator")
    staff_member = user_factory(username="staffer")
    program = service.create_program(_valid_data(), creator)
    program.state = ProgramState.SUBMISSION
    db.session.commit()

    with pytest.raises(ConflictError):
        service.add_staff(program.id, staff_member.id, creator)


def test_add_staff_rejects_user_already_staff(db, user_factory, service):
    creator = user_factory(username="creator")
    staff_member = user_factory(username="staffer")
    program = service.create_program(_valid_data(), creator)
    service.add_staff(program.id, staff_member.id, creator)

    with pytest.raises(ConflictError):
        service.add_staff(program.id, staff_member.id, creator)


def test_add_staff_rejects_non_programmer_requester(db, user_factory, service):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    target = user_factory(username="target")
    program = service.create_program(_valid_data(), creator)

    with pytest.raises(AuthorizationError):
        service.add_staff(program.id, target.id, outsider)


def test_search_programs_returns_all_when_no_criteria(db, user_factory, service):
    creator = user_factory(username="creator")
    service.create_program(_valid_data(name="Spring", startDate="2026-03-01"), creator)
    service.create_program(_valid_data(name="Autumn", startDate="2026-09-01"), creator)

    results = service.search_programs({}, creator)

    assert [p["name"] for p in results] == ["Spring", "Autumn"]


def test_search_programs_sorts_by_date_then_name(db, user_factory, service):
    creator = user_factory(username="creator")
    service.create_program(
        _valid_data(name="B", startDate="2026-01-01", endDate="2026-02-01"), creator
    )
    service.create_program(
        _valid_data(name="A", startDate="2026-01-01", endDate="2026-02-01"), creator
    )
    service.create_program(
        _valid_data(name="C", startDate="2025-01-01", endDate="2025-02-01"), creator
    )

    results = service.search_programs({}, creator)

    assert [p["name"] for p in results] == ["C", "A", "B"]


def test_search_programs_filters_by_name_and_description_with_and_semantics(
    db, user_factory, service
):
    creator = user_factory(username="creator")
    service.create_program(
        _valid_data(name="Spring Classics", description="Old films"), creator
    )
    service.create_program(
        _valid_data(name="Spring Indie", description="New films"), creator
    )

    results = service.search_programs({"name": "spring", "description": "old"}, creator)

    assert [p["name"] for p in results] == ["Spring Classics"]


def test_search_programs_filters_by_date_range(db, user_factory, service):
    creator = user_factory(username="creator")
    service.create_program(
        _valid_data(name="Early", startDate="2026-01-01", endDate="2026-02-01"), creator
    )
    service.create_program(
        _valid_data(name="Late", startDate="2026-11-01", endDate="2026-12-01"), creator
    )

    results = service.search_programs({"startDateFrom": "2026-06-01"}, creator)

    assert [p["name"] for p in results] == ["Late"]


def test_search_programs_redacts_for_outsider(db, user_factory, service):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    service.create_program(_valid_data(), creator)

    results = service.search_programs({}, outsider)

    assert "programmers" not in results[0]
    assert "staff" not in results[0]
    assert "creationDate" not in results[0]


def test_search_programs_full_detail_for_programmer(db, user_factory, service):
    creator = user_factory(username="creator")
    service.create_program(_valid_data(), creator)

    results = service.search_programs({}, creator)

    assert results[0]["programmers"] == [
        {"id": creator.id, "username": creator.username, "fullName": creator.full_name}
    ]
    assert "creationDate" in results[0]


def test_get_program_full_detail_for_programmer(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    dto = service.get_program(program.id, creator)

    assert dto["name"] == "Spring Season"
    assert dto["programmers"] == [
        {"id": creator.id, "username": creator.username, "fullName": creator.full_name}
    ]
    assert "creationDate" in dto


def test_get_program_redacted_for_outsider(db, user_factory, service):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    program = service.create_program(_valid_data(), creator)

    dto = service.get_program(program.id, outsider)

    assert dto["name"] == "Spring Season"
    assert "programmers" not in dto
    assert "staff" not in dto
    assert "creationDate" not in dto


def test_get_program_redacted_for_anonymous_visitor(db, user_factory, service):
    creator = user_factory(username="creator")
    program = service.create_program(_valid_data(), creator)

    dto = service.get_program(program.id, None)

    assert "programmers" not in dto


def test_get_program_unknown_id_raises_not_found(db, service):
    with pytest.raises(NotFoundError):
        service.get_program("does-not-exist", None)
