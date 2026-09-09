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
from app.services.program_service import register_decision_hook


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
            try:
                duration = int(data["filmDurationMinutes"])
            except (TypeError, ValueError):
                raise ValidationError(
                    "filmDurationMinutes must be an integer"
                )

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
        _, screening = self._get_program_and_screening(
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
            try:
                duration = int(data["filmDurationMinutes"])
            except (TypeError, ValueError):
                raise ValidationError(
                    "filmDurationMinutes must be an integer"
                )

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
        _, screening = self._get_program_and_screening(
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
            raise NotFoundError(
                f"User '{user_id}' is not STAFF of program '{program_id}'"
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

        try:
            score = float(data["score"])
        except (TypeError, ValueError):
            raise ValidationError(
                "score must be numeric"
            )

        screening.review_score = score
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

        if screening.state in {
            ScreeningState.SCHEDULED,
            ScreeningState.REJECTED,
        }:
            raise ConflictError(
                "Screening is already in a final state"
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
            if not data["filmTitle"]:
                raise ValidationError(
                    "filmTitle cannot be empty"
                )
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
        _, screening = self._get_program_and_screening(
            program_id,
            screening_id,
        )

        if (
            not self._has_full_access(screening, requester)
            and not self._is_public(screening)
        ):
            raise NotFoundError(
                f"Screening '{screening_id}' not found"
            )

        return self._serialize_screening(
            screening,
            requester,
        )

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

        date_from = filters.get("dateFrom")

        if date_from:
            query = query.filter(
                Screening.start_time
                >= self._parse_datetime(date_from)
            )

        date_to = filters.get("dateTo")

        if date_to:
            query = query.filter(
                Screening.start_time
                <= self._parse_datetime(date_to)
            )

        if filters.get("view") == "timetable":
            screenings = query.order_by(
                Screening.start_time.asc()
            ).all()
        else:
            screenings = query.order_by(
                Screening.film_genres.asc(),
                Screening.film_title.asc(),
            ).all()

        visible = [
            screening
            for screening in screenings
            if (
                self._has_full_access(
                    screening,
                    requester,
                )
                or self._is_public(screening)
            )
        ]

        return [
            self._serialize_screening(
                screening,
                requester,
            )
            for screening in visible
        ]

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

    def _has_full_access(
        self,
        screening,
        requester,
    ):
        if requester is None:
            return False

        if requester.id == screening.submitter_id:
            return True

        if (
            screening.handler_id is not None
            and requester.id == screening.handler_id
        ):
            return True

        return requester in screening.program.programmers

    def _is_public(self, screening):
        return (
            screening.program.state
            == ProgramState.ANNOUNCED
            and screening.state
            == ScreeningState.SCHEDULED
        )

    def _serialize_screening(
        self,
        screening,
        requester,
    ):
        if self._has_full_access(
            screening,
            requester,
        ):
            return {
                "id": screening.id,
                "creationDate": (
                    screening.creation_date.isoformat()
                    if screening.creation_date
                    else None
                ),
                "state": screening.state.value,
                "filmTitle": screening.film_title,
                "filmCast": screening.film_cast,
                "filmGenres": screening.film_genres,
                "filmDurationMinutes": (
                    screening.film_duration_minutes
                ),
                "auditoriumName": (
                    screening.auditorium_name
                ),
                "startTime": (
                    screening.start_time.isoformat()
                    if screening.start_time
                    else None
                ),
                "endTime": (
                    screening.end_time.isoformat()
                    if screening.end_time
                    else None
                ),
                "submitterId": screening.submitter_id,
                "handlerId": screening.handler_id,
                "reviewScore": screening.review_score,
                "reviewComments": (
                    screening.review_comments
                ),
                "rejectionReason": (
                    screening.rejection_reason
                ),
            }

        return {
            "id": screening.id,
            "filmTitle": screening.film_title,
            "filmCast": screening.film_cast,
            "filmGenres": screening.film_genres,
            "auditoriumName": screening.auditorium_name,
            "startTime": (
                screening.start_time.isoformat()
                if screening.start_time
                else None
            ),
            "endTime": (
                screening.end_time.isoformat()
                if screening.end_time
                else None
            ),
            "state": screening.state.value,
        }

    def _parse_datetime(
        self,
        value,
    ):
        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            raise ValidationError(
                "Invalid datetime format"
            )

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except ValueError:
            raise ValidationError(
                "Invalid datetime format"
            )


def _auto_reject_unsubmitted_screenings(program):
    screenings = Screening.query.filter_by(
        program_id=program.id,
        state=ScreeningState.APPROVED,
        final_submitted=False,
    ).all()

    for screening in screenings:
        screening.state = ScreeningState.REJECTED
        screening.rejection_reason = (
            "Automatically rejected: final submission was not completed"
        )


register_decision_hook(
    _auto_reject_unsubmitted_screenings
)


screening_service = ScreeningService()