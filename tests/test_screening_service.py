from datetime import datetime

import pytest

from app.models.program import ProgramState
from app.models.screening import Screening, ScreeningState
from app.services.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.program_service import ProgramService
from app.services.screening_service import ScreeningService


@pytest.fixture
def program_service():
    return ProgramService()


@pytest.fixture
def service():
    return ScreeningService()


def _program_data(name="Test Program"):
    return {
        "name": name,
        "description": "Test cinema program",
        "startDate": "2026-01-01",
        "endDate": "2026-12-31",
    }


def _screening_data(**overrides):
    data = {
        "filmTitle": "Interstellar",
        "filmCast": "Matthew McConaughey Anne Hathaway",
        "filmGenres": "Science Fiction",
        "filmDurationMinutes": 169,
        "auditoriumName": "Auditorium A",
        "startTime": "2026-05-10T18:00:00",
    }

    data.update(overrides)
    return data


def _create_program(program_service, programmer, name="Test Program"):
    return program_service.create_program(
        _program_data(name),
        programmer,
    )


def _create_screening(service, program, submitter, **overrides):
    return service.create_screening(
        program.id,
        _screening_data(**overrides),
        submitter,
    )


# ---------------------------------------------------------------------------
# CREATE SCREENING
# ---------------------------------------------------------------------------


def test_create_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    assert screening.id is not None
    assert screening.creation_date is not None
    assert screening.state == ScreeningState.CREATED

    assert screening.program_id == program.id
    assert screening.submitter_id == submitter.id

    assert screening.film_title == "Interstellar"
    assert screening.film_duration_minutes == 169

    assert screening.handler_id is None
    assert screening.end_time is None


def test_create_screening_missing_film_title(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    with pytest.raises(ValidationError):
        service.create_screening(
            program.id,
            {"filmTitle": ""},
            submitter,
        )


def test_create_screening_unknown_program(
    db,
    user_factory,
    service,
):
    submitter = user_factory()

    with pytest.raises(NotFoundError):
        service.create_screening(
            "does-not-exist",
            _screening_data(),
            submitter,
        )


def test_create_screening_rejects_programmer(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        program_service,
        programmer,
    )

    with pytest.raises(AuthorizationError):
        service.create_screening(
            program.id,
            _screening_data(),
            programmer,
        )


def test_create_screening_requires_authenticated_user(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        program_service,
        programmer,
    )

    with pytest.raises(AuthorizationError):
        service.create_screening(
            program.id,
            _screening_data(),
            None,
        )


# ---------------------------------------------------------------------------
# UPDATE SCREENING
# ---------------------------------------------------------------------------


def test_update_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    updated = service.update_screening(
        program.id,
        screening.id,
        {
            "filmTitle": "Updated Film",
            "auditoriumName": "Auditorium B",
        },
        submitter,
    )

    assert updated.film_title == "Updated Film"
    assert updated.auditorium_name == "Auditorium B"


def test_update_screening_rejects_non_submitter(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    outsider = user_factory(username="outsider")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    with pytest.raises(AuthorizationError):
        service.update_screening(
            program.id,
            screening.id,
            {"filmTitle": "Illegal Update"},
            outsider,
        )


def test_update_screening_rejects_after_created(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    db.session.commit()

    with pytest.raises(ConflictError):
        service.update_screening(
            program.id,
            screening.id,
            {"filmTitle": "Too Late"},
            submitter,
        )


# ---------------------------------------------------------------------------
# SUBMIT SCREENING
# ---------------------------------------------------------------------------


def test_submit_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SUBMISSION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    submitted = service.submit_screening(
        program.id,
        screening.id,
        submitter,
    )

    assert submitted.state == ScreeningState.SUBMITTED

    expected_end = datetime.fromisoformat(
        "2026-05-10T20:49:00"
    )

    assert submitted.end_time == expected_end


def test_submit_screening_wrong_program_state(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    with pytest.raises(ConflictError):
        service.submit_screening(
            program.id,
            screening.id,
            submitter,
        )


def test_submit_screening_incomplete(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SUBMISSION
    db.session.commit()

    screening = service.create_screening(
        program.id,
        {
            "filmTitle": "Incomplete Film",
        },
        submitter,
    )

    with pytest.raises(ConflictError):
        service.submit_screening(
            program.id,
            screening.id,
            submitter,
        )


def test_submit_screening_rejects_non_submitter(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    outsider = user_factory(username="outsider")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SUBMISSION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    with pytest.raises(AuthorizationError):
        service.submit_screening(
            program.id,
            screening.id,
            outsider,
        )


# ---------------------------------------------------------------------------
# WITHDRAW
# ---------------------------------------------------------------------------


def test_withdraw_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening_id = screening.id

    service.withdraw_screening(
        program.id,
        screening.id,
        submitter,
    )

    assert db.session.get(
        Screening,
        screening_id,
    ) is None


def test_withdraw_rejects_submitted_screening(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    db.session.commit()

    with pytest.raises(ConflictError):
        service.withdraw_screening(
            program.id,
            screening.id,
            submitter,
        )


# ---------------------------------------------------------------------------
# ASSIGN HANDLER
# ---------------------------------------------------------------------------


def test_assign_handler_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")

    program = _create_program(
        program_service,
        programmer,
    )

    program_service.add_staff(
        program.id,
        staff.id,
        programmer,
    )

    program.state = ProgramState.ASSIGNMENT
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    db.session.commit()

    assigned = service.assign_handler(
        program.id,
        screening.id,
        staff.id,
        programmer,
    )

    assert assigned.handler_id == staff.id
    assert assigned.handler == staff


def test_assign_handler_rejects_non_staff(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    outsider = user_factory(username="outsider")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.ASSIGNMENT
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    db.session.commit()

    with pytest.raises(
        (AuthorizationError, NotFoundError)
    ):
        service.assign_handler(
            program.id,
            screening.id,
            outsider.id,
            programmer,
        )


def test_assign_handler_rejects_non_programmer(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")
    outsider = user_factory(username="outsider")

    program = _create_program(
        program_service,
        programmer,
    )

    program_service.add_staff(
        program.id,
        staff.id,
        programmer,
    )

    program.state = ProgramState.ASSIGNMENT
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    db.session.commit()

    with pytest.raises(AuthorizationError):
        service.assign_handler(
            program.id,
            screening.id,
            staff.id,
            outsider,
        )


# ---------------------------------------------------------------------------
# REVIEW
# ---------------------------------------------------------------------------


def test_review_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")

    program = _create_program(
        program_service,
        programmer,
    )

    program_service.add_staff(
        program.id,
        staff.id,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    screening.handler = staff

    program.state = ProgramState.REVIEW

    db.session.commit()

    reviewed = service.review_screening(
        program.id,
        screening.id,
        {
            "score": 8.5,
            "comments": "Strong technical quality",
        },
        staff,
    )

    assert reviewed.state == ScreeningState.REVIEWED
    assert reviewed.review_score == 8.5
    assert reviewed.review_comments == "Strong technical quality"


def test_review_requires_assigned_handler(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    handler = user_factory(username="handler")
    other_staff = user_factory(username="otherstaff")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    screening.handler = handler

    program.state = ProgramState.REVIEW

    db.session.commit()

    with pytest.raises(AuthorizationError):
        service.review_screening(
            program.id,
            screening.id,
            {
                "score": 7,
                "comments": "No access",
            },
            other_staff,
        )


def test_review_missing_comments(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.SUBMITTED
    screening.handler = staff

    program.state = ProgramState.REVIEW

    db.session.commit()

    with pytest.raises(ValidationError):
        service.review_screening(
            program.id,
            screening.id,
            {
                "score": 9,
            },
            staff,
        )


# ---------------------------------------------------------------------------
# APPROVE
# ---------------------------------------------------------------------------


def test_approve_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SCHEDULING
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.REVIEWED
    db.session.commit()

    approved = service.approve_screening(
        program.id,
        screening.id,
        {
            "notes": "Adjust subtitles",
        },
        programmer,
    )

    assert approved.state == ScreeningState.APPROVED
    assert approved.approval_notes == "Adjust subtitles"


def test_approve_requires_programmer(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SCHEDULING
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.REVIEWED
    db.session.commit()

    with pytest.raises(AuthorizationError):
        service.approve_screening(
            program.id,
            screening.id,
            {},
            submitter,
        )


# ---------------------------------------------------------------------------
# REJECT
# ---------------------------------------------------------------------------


def test_reject_screening_success_during_scheduling(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SCHEDULING
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.REVIEWED
    db.session.commit()

    rejected = service.reject_screening(
        program.id,
        screening.id,
        {
            "reason": "Technical quality too low",
        },
        programmer,
    )

    assert rejected.state == ScreeningState.REJECTED
    assert rejected.rejection_reason == "Technical quality too low"


def test_reject_requires_reason(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.SCHEDULING
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.REVIEWED
    db.session.commit()

    with pytest.raises(ValidationError):
        service.reject_screening(
            program.id,
            screening.id,
            {},
            programmer,
        )


# ---------------------------------------------------------------------------
# FINAL SUBMISSION
# ---------------------------------------------------------------------------


def test_final_submit_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.FINAL_SUBMISSION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    db.session.commit()

    final = service.final_submit_screening(
        program.id,
        screening.id,
        {
            "auditoriumName": "Final Auditorium",
        },
        submitter,
    )

    assert final.state == ScreeningState.APPROVED
    assert final.final_submitted is True
    assert final.auditorium_name == "Final Auditorium"


def test_final_submit_requires_submitter(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    outsider = user_factory(username="outsider")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.FINAL_SUBMISSION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    db.session.commit()

    with pytest.raises(AuthorizationError):
        service.final_submit_screening(
            program.id,
            screening.id,
            {},
            outsider,
        )


# ---------------------------------------------------------------------------
# ACCEPT
# ---------------------------------------------------------------------------


def test_accept_screening_success(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.DECISION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    screening.final_submitted = True

    db.session.commit()

    accepted = service.accept_screening(
        program.id,
        screening.id,
        programmer,
    )

    assert accepted.state == ScreeningState.SCHEDULED


def test_accept_rejects_without_final_submission(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    program.state = ProgramState.DECISION
    db.session.commit()

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    screening.final_submitted = False

    db.session.commit()

    with pytest.raises(ConflictError):
        service.accept_screening(
            program.id,
            screening.id,
            programmer,
        )


# ---------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------


def test_search_screenings_returns_matching_title(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    service.create_screening(
        program.id,
        _screening_data(
            filmTitle="Star Wars",
        ),
        submitter,
    )

    service.create_screening(
        program.id,
        _screening_data(
            filmTitle="Interstellar",
        ),
        submitter,
    )

    results = service.search_screenings(
        program.id,
        {
            "filmTitle": "star war",
        },
        submitter,
    )

    assert len(results) == 1

    result = results[0]

    if isinstance(result, dict):
        assert result["filmTitle"] == "Star Wars"
    else:
        assert result.film_title == "Star Wars"


def test_search_screenings_uses_and_semantics(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    service.create_screening(
        program.id,
        _screening_data(
            filmTitle="Star Wars",
            filmGenres="Science Fiction",
        ),
        submitter,
    )

    service.create_screening(
        program.id,
        _screening_data(
            filmTitle="Star Wars Documentary",
            filmGenres="Documentary",
        ),
        submitter,
    )

    results = service.search_screenings(
        program.id,
        {
            "filmTitle": "star",
            "genre": "science",
        },
        submitter,
    )

    assert len(results) == 1


def test_search_screenings_unknown_program(
    db,
    service,
):
    with pytest.raises(NotFoundError):
        service.search_screenings(
            "does-not-exist",
            {},
            None,
        )


# ---------------------------------------------------------------------------
# GET / VIEW SERVICE
# ---------------------------------------------------------------------------


def test_get_screening_returns_existing_screening(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        program_service,
        programmer,
    )

    screening = _create_screening(
        service,
        program,
        submitter,
    )

    result = service.get_screening(
        program.id,
        screening.id,
        submitter,
    )

    if isinstance(result, dict):
        assert result["id"] == screening.id
        assert result["filmTitle"] == "Interstellar"
    else:
        assert result.id == screening.id
        assert result.film_title == "Interstellar"


def test_get_screening_unknown_id(
    db,
    user_factory,
    service,
    program_service,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        program_service,
        programmer,
    )

    with pytest.raises(NotFoundError):
        service.get_screening(
            program.id,
            "does-not-exist",
            programmer,
        )