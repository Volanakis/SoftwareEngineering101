from datetime import date

from app.extensions import db
from app.models.program import Program
from app.models.screening import Screening, ScreeningState


def test_screening_creation(app, user_factory):
    with app.app_context():
        submitter = user_factory(
            username="submitter1",
            full_name="Test Submitter",
        )

        program = Program(
            name="Test Program",
            description="Test Description",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 20),
        )

        db.session.add(program)
        db.session.commit()

        screening = Screening(
            program_id=program.id,
            submitter_id=submitter.id,
            film_title="Test Film",
        )

        db.session.add(screening)
        db.session.commit()

        assert screening.id is not None
        assert screening.creation_date is not None
        assert screening.state == ScreeningState.CREATED

        assert screening.program_id == program.id
        assert screening.submitter_id == submitter.id

        assert screening.handler_id is None
        assert screening.final_submitted is False

        assert screening.film_title == "Test Film"


def test_screening_relationships(app, user_factory):
    with app.app_context():
        submitter = user_factory(
            username="submitter2",
            full_name="Submitter Two",
        )

        handler = user_factory(
            username="handler1",
            full_name="Handler One",
        )

        program = Program(
            name="Second Program",
            description="Another Program",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
        )

        db.session.add(program)
        db.session.commit()

        screening = Screening(
            program=program,
            submitter=submitter,
            handler=handler,
            film_title="Relationship Test",
        )

        db.session.add(screening)
        db.session.commit()

        assert screening.program == program
        assert screening.submitter == submitter
        assert screening.handler == handler