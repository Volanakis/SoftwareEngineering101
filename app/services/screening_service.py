from datetime import datetime, timedelta

from app.extensions import db
from app.models.program import Program, ProgramRole, ProgramState, RoleType
from app.models.screening import Screening, ScreeningState
from app.models.user import User
from app.services.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class ScreeningService:

    def create_screening(self, program_id, data, requester):
        program = db.session.get(Program, program_id)

        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester is None:
            raise AuthorizationError("Authentication is required")

        if requester in program.programmers:
            raise AuthorizationError(
                "A PROGRAMMER cannot submit a screening to their own program"
            )

        film_title = data.get("filmTitle")

        if not film_title:
            raise ValidationError("Missing required field: filmTitle")

        screening = Screening(
            program=program,
            submitter=requester,
            film_title=film_title,
        )

        if "filmCast" in data:
            screening.film_cast = data["filmCast"]

        if "filmGenres" in data:
            screening.film_genres = data["filmGenres"]

        if "filmDurationMinutes" in data:
            screening.film_duration_minutes = int(
                data["filmDurationMinutes"]
            )

        if "auditoriumName" in data:
            screening.auditorium_name = data["auditoriumName"]

        if "startTime" in data:
            screening.start_time = self._parse_datetime(
                data["startTime"]
            )

        db.session.add(screening)
        db.session.commit()

        return screening

    def update_screening(
        self,
        program_id,
        screening_id,
        data,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_submitter(screening, requester)

        if screening.state != ScreeningState.CREATED:
            raise ConflictError(
                "Screening can only be updated while in CREATED state"
            )

        if "filmTitle" in data:
            if not data["filmTitle"]:
                raise ValidationError("filmTitle cannot be empty")

            screening.film_title = data["filmTitle"]

        if "filmCast" in data:
            screening.film_cast = data["filmCast"]

        if "filmGenres" in data:
            screening.film_genres = data["filmGenres"]

        if "filmDurationMinutes" in data:
            duration = int(data["filmDurationMinutes"])

            if duration <= 0:
                raise ValidationError(
                    "filmDurationMinutes must be greater than zero"
                )

            screening.film_duration_minutes = duration

        if "auditoriumName" in data:
            screening.auditorium_name = data["auditoriumName"]

        if "startTime" in data:
            screening.start_time = self._parse_datetime(
                data["startTime"]
            )

        db.session.commit()

        return screening

    def submit_screening(
        self,
        program_id,
        screening_id,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_submitter(screening, requester)

        if program.state != ProgramState.SUBMISSION:
            raise ConflictError(
                "Screening submission is allowed only during SUBMISSION"
            )

        if screening.state != ScreeningState.CREATED:
            raise ConflictError(
                "Only a CREATED screening can be submitted"
            )

        if not screening.film_title:
            raise ConflictError("Missing film title")

        if not screening.auditorium_name:
            raise ConflictError("Missing auditorium")

        if screening.film_duration_minutes is None:
            raise ConflictError("Missing film duration")

        if screening.start_time is None:
            raise ConflictError("Missing start time")

        screening.end_time = (
            screening.start_time
            + timedelta(
                minutes=screening.film_duration_minutes
            )
        )

        screening.state = ScreeningState.SUBMITTED

        db.session.commit()

        return screening

    def withdraw_screening(
        self,
        program_id,
        screening_id,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_submitter(screening, requester)

        if screening.state != ScreeningState.CREATED:
            raise ConflictError(
                "Only a CREATED screening can be withdrawn"
            )

        db.session.delete(screening)
        db.session.commit()

    def assign_handler(
        self,
        program_id,
        screening_id,
        user_id,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_programmer(program, requester)

        if program.state != ProgramState.ASSIGNMENT:
            raise ConflictError(
                "Handler assignment is allowed only during ASSIGNMENT"
            )

        if screening.handler_id is not None:
            raise ConflictError(
                "Screening already has a handler"
            )

        user = db.session.get(User, user_id)

        if user is None:
            raise NotFoundError(
                f"User '{user_id}' not found"
            )

        role = ProgramRole.query.filter_by(
            program_id=program.id,
            user_id=user.id,
            role_type=RoleType.STAFF,
        ).first()

        if role is None:
            raise AuthorizationError(
                "User is not STAFF of this program"
            )

        screening.handler = user

        db.session.commit()

        return screening

    def review_screening(
        self,
        program_id,
        screening_id,
        data,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        if (
            requester is None
            or screening.handler_id != requester.id
        ):
            raise AuthorizationError(
                "Only the assigned STAFF member can review this screening"
            )

        if program.state != ProgramState.REVIEW:
            raise ConflictError(
                "Review is allowed only during REVIEW"
            )

        if screening.state != ScreeningState.SUBMITTED:
            raise ConflictError(
                "Only a SUBMITTED screening can be reviewed"
            )

        if "score" not in data:
            raise ValidationError(
                "Missing required field: score"
            )

        if not data.get("comments"):
            raise ValidationError(
                "Missing required field: comments"
            )

        screening.review_score = float(
            data["score"]
        )

        screening.review_comments = data["comments"]

        screening.state = ScreeningState.REVIEWED

        db.session.commit()

        return screening

    def approve_screening(
        self,
        program_id,
        screening_id,
        data,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_programmer(program, requester)

        if program.state != ProgramState.SCHEDULING:
            raise ConflictError(
                "Approval is allowed only during SCHEDULING"
            )

        if screening.state != ScreeningState.REVIEWED:
            raise ConflictError(
                "Only a REVIEWED screening can be approved"
            )

        screening.approval_notes = data.get("notes")

        screening.state = ScreeningState.APPROVED

        db.session.commit()

        return screening

    def reject_screening(
        self,
        program_id,
        screening_id,
        data,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_programmer(program, requester)

        reason = data.get("reason")

        if not reason:
            raise ValidationError(
                "Missing required field: reason"
            )

        if program.state not in {
            ProgramState.SCHEDULING,
            ProgramState.DECISION,
        }:
            raise ConflictError(
                "Rejection is allowed only during SCHEDULING or DECISION"
            )

        screening.rejection_reason = reason

        screening.state = ScreeningState.REJECTED

        db.session.commit()

        return screening

    def final_submit_screening(
        self,
        program_id,
        screening_id,
        data,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_submitter(
            screening,
            requester,
        )

        if program.state != ProgramState.FINAL_SUBMISSION:
            raise ConflictError(
                "Final submission is allowed only during FINAL_SUBMISSION"
            )

        if screening.state != ScreeningState.APPROVED:
            raise ConflictError(
                "Only an APPROVED screening can be finally submitted"
            )

        if "filmTitle" in data:
            screening.film_title = data["filmTitle"]

        if "filmCast" in data:
            screening.film_cast = data["filmCast"]

        if "filmGenres" in data:
            screening.film_genres = data["filmGenres"]

        if "auditoriumName" in data:
            screening.auditorium_name = data["auditoriumName"]

        if "startTime" in data:
            screening.start_time = self._parse_datetime(
                data["startTime"]
            )

        screening.final_submitted = True

        if (
            screening.start_time is not None
            and screening.film_duration_minutes is not None
        ):
            screening.end_time = (
                screening.start_time
                + timedelta(
                    minutes=screening.film_duration_minutes
                )
            )

        db.session.commit()

        return screening

    def accept_screening(
        self,
        program_id,
        screening_id,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        self._require_programmer(
            program,
            requester,
        )

        if program.state != ProgramState.DECISION:
            raise ConflictError(
                "Acceptance is allowed only during DECISION"
            )

        if screening.state != ScreeningState.APPROVED:
            raise ConflictError(
                "Only an APPROVED screening can be accepted"
            )

        if not screening.final_submitted:
            raise ConflictError(
                "Screening has not been finally submitted"
            )

        screening.state = ScreeningState.SCHEDULED

        db.session.commit()

        return screening

    def get_screening(
        self,
        program_id,
        screening_id,
        requester,
    ):
        program, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        return screening

    def search_screenings(
        self,
        program_id,
        filters,
        requester,
    ):
        program = db.session.get(
            Program,
            program_id,
        )

        if program is None:
            raise NotFoundError(
                f"Program '{program_id}' not found"
            )

        query = Screening.query.filter_by(
            program_id=program.id
        )

        title = filters.get("filmTitle")

        if title:
            for word in title.split():
                query = query.filter(
                    Screening.film_title.ilike(
                        f"%{word}%"
                    )
                )

        cast = filters.get("cast")

        if cast:
            for word in cast.split():
                query = query.filter(
                    Screening.film_cast.ilike(
                        f"%{word}%"
                    )
                )

        genre = filters.get("genre")

        if genre:
            for word in genre.split():
                query = query.filter(
                    Screening.film_genres.ilike(
                        f"%{word}%"
                    )
                )

        return query.order_by(
            Screening.film_genres.asc(),
            Screening.film_title.asc(),
        ).all()

    def _get_program_and_screening(
        self,
        program_id,
        screening_id,
    ):
        program = db.session.get(
            Program,
            program_id,
        )

        if program is None:
            raise NotFoundError(
                f"Program '{program_id}' not found"
            )

        screening = db.session.get(
            Screening,
            screening_id,
        )

        if (
            screening is None
            or screening.program_id != program.id
        ):
            raise NotFoundError(
                f"Screening '{screening_id}' not found"
            )

        return program, screening

    def _require_submitter(
        self,
        screening,
        requester,
    ):
        if (
            requester is None
            or requester.id != screening.submitter_id
        ):
            raise AuthorizationError(
                "Only the SUBMITTER can perform this action"
            )

    def _require_programmer(
        self,
        program,
        requester,
    ):
        if (
            requester is None
            or requester not in program.programmers
        ):
            raise AuthorizationError(
                "Only a PROGRAMMER of this program can perform this action"
            )

    def _parse_datetime(
        self,
        value,
    ):
        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except (ValueError, AttributeError):
            raise ValidationError(
                "Invalid datetime format"
            )


screening_service = ScreeningService()