from app.extensions import db
from app.models.program import ProgramState
from app.models.screening import ScreeningState
from app.services.program_service import ProgramService
from app.services.screening_service import ScreeningService


def _program_data(name):
    return {
        "name": name,
        "description": "Decision transition test program",
        "startDate": "2026-01-01",
        "endDate": "2026-12-31",
    }


def _screening_data():
    return {
        "filmTitle": "Decision Test Film",
        "filmCast": "Actor One Actor Two",
        "filmGenres": "Drama",
        "filmDurationMinutes": 120,
        "auditoriumName": "Auditorium A",
        "startTime": "2026-05-10T18:00:00",
    }


def test_transition_to_decision_auto_rejects_unsubmitted_screening(
    db,
    user_factory,
):
    program_service = ProgramService()
    screening_service = ScreeningService()

    programmer = user_factory(
        username="decision-programmer"
    )

    submitter = user_factory(
        username="decision-submitter"
    )

    program = program_service.create_program(
        _program_data(
            "Auto Reject Program"
        ),
        programmer,
    )

    screening = screening_service.create_screening(
        program.id,
        _screening_data(),
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    screening.final_submitted = False

    program.state = ProgramState.FINAL_SUBMISSION

    db.session.commit()

    program_service.transition_program(
        program.id,
        "DECISION",
        programmer,
    )

    db.session.refresh(screening)
    db.session.refresh(program)

    assert (
        program.state
        == ProgramState.DECISION
    )

    assert (
        screening.state
        == ScreeningState.REJECTED
    )

    assert screening.rejection_reason == (
        "Automatically rejected: "
        "final submission was not completed"
    )


def test_transition_to_decision_keeps_final_submitted_screening_approved(
    db,
    user_factory,
):
    program_service = ProgramService()
    screening_service = ScreeningService()

    programmer = user_factory(
        username="final-programmer"
    )

    submitter = user_factory(
        username="final-submitter"
    )

    program = program_service.create_program(
        _program_data(
            "Final Submission Program"
        ),
        programmer,
    )

    screening = screening_service.create_screening(
        program.id,
        _screening_data(),
        submitter,
    )

    screening.state = ScreeningState.APPROVED
    screening.final_submitted = True

    program.state = ProgramState.FINAL_SUBMISSION

    db.session.commit()

    program_service.transition_program(
        program.id,
        "DECISION",
        programmer,
    )

    db.session.refresh(screening)
    db.session.refresh(program)

    assert (
        program.state
        == ProgramState.DECISION
    )

    assert (
        screening.state
        == ScreeningState.APPROVED
    )

    assert screening.rejection_reason is None


def test_transition_to_decision_rejects_only_unsubmitted_screenings(
    db,
    user_factory,
):
    program_service = ProgramService()
    screening_service = ScreeningService()

    programmer = user_factory(
        username="mixed-programmer"
    )

    first_submitter = user_factory(
        username="first-submitter"
    )

    second_submitter = user_factory(
        username="second-submitter"
    )

    program = program_service.create_program(
        _program_data(
            "Mixed Decision Program"
        ),
        programmer,
    )

    unsubmitted = screening_service.create_screening(
        program.id,
        {
            **_screening_data(),
            "filmTitle": "Unsubmitted Film",
        },
        first_submitter,
    )

    final_submitted = screening_service.create_screening(
        program.id,
        {
            **_screening_data(),
            "filmTitle": "Final Submitted Film",
        },
        second_submitter,
    )

    unsubmitted.state = ScreeningState.APPROVED
    unsubmitted.final_submitted = False

    final_submitted.state = ScreeningState.APPROVED
    final_submitted.final_submitted = True

    program.state = ProgramState.FINAL_SUBMISSION

    db.session.commit()

    program_service.transition_program(
        program.id,
        "DECISION",
        programmer,
    )

    db.session.refresh(unsubmitted)
    db.session.refresh(final_submitted)

    assert (
        unsubmitted.state
        == ScreeningState.REJECTED
    )

    assert (
        final_submitted.state
        == ScreeningState.APPROVED
    )