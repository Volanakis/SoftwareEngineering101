import logging
from datetime import date, datetime

from sqlalchemy import and_, or_
from app.extensions import db
from app.models.program import Program, ProgramRole, ProgramState, RoleType
from app.models.user import User
from app.services.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

REQUIRED_CREATE_FIELDS = ("name", "description", "startDate", "endDate")

# ΛΑ-2.8: strictly sequential lifecycle, no rollback or skipping a step.
PROGRAM_STATE_ORDER = [
    ProgramState.CREATED,
    ProgramState.SUBMISSION,
    ProgramState.ASSIGNMENT,
    ProgramState.REVIEW,
    ProgramState.SCHEDULING,
    ProgramState.FINAL_SUBMISSION,
    ProgramState.DECISION,
    ProgramState.ANNOUNCED,
]

# ΛΑ-2.8.6: entering DECISION must auto-reject APPROVED-but-not-finally-submitted
# screenings. ProgramService has no dependency on the Screening model (Person B), so
# that behavior is wired in via this hook registry instead of a direct import.
_decision_transition_hooks = []


def register_decision_hook(hook):
    """Register callable(program) to run when a program transitions into DECISION."""
    _decision_transition_hooks.append(hook)


class ProgramService:
    def create_program(self, data, creator):
        """ΛΑ-2.1: create a program; the creator is auto-registered as PROGRAMMER."""
        if not isinstance(data, dict):
            raise ValidationError("Program data must be a JSON object")
        missing = [field for field in REQUIRED_CREATE_FIELDS if not data.get(field)]
        if missing:
            raise ValidationError(f"Missing required field(s): {', '.join(missing)}")

        name = data["name"].strip() if isinstance(data["name"], str) else data["name"]
        description = (
            data["description"].strip()
            if isinstance(data["description"], str)
            else data["description"]
        )
        if not name or not isinstance(name, str):
            raise ValidationError("name must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValidationError("description must be a non-empty string")

        if (
            Program.query.filter(db.func.lower(Program.name) == name.lower()).first()
            is not None
        ):
            raise ConflictError(f"Program name '{name}' is already taken")

        start_date = _as_date(data["startDate"])
        end_date = _as_date(data["endDate"])
        _validate_date_order(start_date, end_date)

        program = Program(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            creator=creator,
        )
        db.session.add(program)
        db.session.flush()

        db.session.add(
            ProgramRole(program=program, user=creator, role_type=RoleType.PROGRAMMER)
        )
        db.session.commit()
        logger.info(
            "Program created | program_id=%s | creator_id=%s", program.id, creator.id
        )
        return program

    def update_program(self, program_id, data, requester):
        """ΛΑ-2.2: update name/description/dates. Only a PROGRAMMER of this program may
        update it, and only before it reaches ANNOUNCED. PROGRAMMERS/STAFF set changes go
        through add_programmer/add_staff (ΛΑ-2.3/2.4) instead of this method, so the
        creator can never be dropped here (ΛΑ-2.2.3)."""
        if not isinstance(data, dict):
            raise ValidationError("Program data must be a JSON object")
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError("Only a PROGRAMMER of this program can update it")

        if program.state == ProgramState.ANNOUNCED:
            raise ConflictError("Program is ANNOUNCED and can no longer be updated")

        new_name = program.name
        new_description = program.description
        new_start_date = program.start_date
        new_end_date = program.end_date

        if "name" in data:
            if not isinstance(data["name"], str) or not data["name"].strip():
                raise ValidationError("name must be a non-empty string")
            new_name = data["name"].strip()
            if (
                new_name != program.name
                and Program.query.filter(
                    db.func.lower(Program.name) == new_name.lower(),
                    Program.id != program.id,
                ).first()
                is not None
            ):
                raise ConflictError(f"Program name '{new_name}' is already taken")

        if "description" in data:
            if (
                not isinstance(data["description"], str)
                or not data["description"].strip()
            ):
                raise ValidationError("description must be a non-empty string")
            new_description = data["description"].strip()

        if "startDate" in data:
            new_start_date = _as_date(data["startDate"])

        if "endDate" in data:
            new_end_date = _as_date(data["endDate"])

        _validate_date_order(new_start_date, new_end_date)
        program.name = new_name
        program.description = new_description
        program.start_date = new_start_date
        program.end_date = new_end_date

        db.session.commit()
        logger.info(
            "Program updated | program_id=%s | requester_id=%s",
            program.id,
            requester.id,
        )
        return program

    def add_programmer(self, program_id, user_id, requester):
        """ΛΑ-2.3: add a PROGRAMMER; the user must not already hold a role in this program."""
        program, user = self._require_programmer_and_target_user(
            program_id, user_id, requester
        )
        self._ensure_user_has_no_role(program, user)

        db.session.add(
            ProgramRole(program=program, user=user, role_type=RoleType.PROGRAMMER)
        )
        db.session.commit()
        logger.info(
            "PROGRAMMER added | program_id=%s | user_id=%s | requester_id=%s",
            program.id,
            user.id,
            requester.id,
        )
        return program

    def add_staff(self, program_id, user_id, requester):
        """ΛΑ-2.4: add STAFF; frozen once the program leaves CREATED (enters SUBMISSION+)."""
        program, user = self._require_programmer_and_target_user(
            program_id, user_id, requester
        )

        if program.state != ProgramState.CREATED:
            raise ConflictError("STAFF set is frozen once the program leaves CREATED")

        self._ensure_user_has_no_role(program, user)

        db.session.add(ProgramRole(program=program, user=user, role_type=RoleType.STAFF))
        db.session.commit()
        logger.info(
            "STAFF added | program_id=%s | user_id=%s | requester_id=%s",
            program.id,
            user.id,
            requester.id,
        )
        return program

    def remove_role(self, program_id, user_id, requester):
        """Remove a PROGRAMMER or STAFF assignment while preserving invariants."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError("Only a PROGRAMMER of this program can remove roles")

        if program.state == ProgramState.ANNOUNCED:
            raise ConflictError("Program is ANNOUNCED and can no longer be updated")

        role = ProgramRole.query.filter_by(
            program_id=program.id, user_id=user_id
        ).first()
        if role is None:
            raise NotFoundError(
                f"User '{user_id}' has no role in program '{program_id}'"
            )

        if user_id == program.creator_id:
            raise ConflictError("The program creator cannot be removed from PROGRAMMERs")

        if role.role_type == RoleType.STAFF and program.state != ProgramState.CREATED:
            raise ConflictError("STAFF set is frozen once the program leaves CREATED")

        db.session.delete(role)
        db.session.commit()
        logger.info(
            "Role removed | program_id=%s | user_id=%s | requester_id=%s",
            program.id,
            user_id,
            requester.id,
        )

    def _require_programmer_and_target_user(self, program_id, user_id, requester):
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError("Only a PROGRAMMER of this program can add roles")

        if program.state == ProgramState.ANNOUNCED:
            raise ConflictError("Program is ANNOUNCED and can no longer be updated")

        user = db.session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User '{user_id}' not found")

        return program, user

    def _ensure_user_has_no_role(self, program, user):
        existing = ProgramRole.query.filter_by(program_id=program.id, user_id=user.id).first()
        if existing is not None:
            raise ConflictError(
                f"User '{user.id}' already has role {existing.role_type.value} in this program"
            )

        from app.models.screening import Screening

        if Screening.query.filter_by(
            program_id=program.id, submitter_id=user.id
        ).first() is not None:
            raise ConflictError(
                f"User '{user.id}' is already a SUBMITTER in this program"
            )

    def get_program(self, program_id, requester):
        """ΛΑ-2.6: view a program, redacted per the requester's role."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if not _can_view_program(program, requester):
            raise NotFoundError(f"Program '{program_id}' not found")

        return _serialize_program(program, requester)

    def search_programs(self, filters, requester):
        """ΛΑ-2.5: AND-combined filters, redacted per role, sorted by date then name.

        Visibility is applied before serialization: outsiders see announced programs
        only, while a program's PROGRAMMER can see it throughout its lifecycle.
        """
        query = Program.query

        if requester is None:
            query = query.filter(Program.state == ProgramState.ANNOUNCED)
        else:
            query = query.filter(
                or_(
                    Program.state == ProgramState.ANNOUNCED,
                    Program.roles.any(
                        and_(
                            ProgramRole.user_id == requester.id,
                            ProgramRole.role_type == RoleType.PROGRAMMER,
                        )
                    ),
                )
            )

        name = filters.get("name")
        if name:
            query = query.filter(Program.name.ilike(f"%{name}%"))

        description = filters.get("description")
        if description:
            query = query.filter(Program.description.ilike(f"%{description}%"))

        start_date_from = filters.get("startDateFrom")
        if start_date_from:
            query = query.filter(Program.start_date >= _as_date(start_date_from))

        start_date_to = filters.get("startDateTo")
        if start_date_to:
            query = query.filter(Program.start_date <= _as_date(start_date_to))

        end_date_from = filters.get("endDateFrom")
        if end_date_from:
            query = query.filter(Program.end_date >= _as_date(end_date_from))

        end_date_to = filters.get("endDateTo")
        if end_date_to:
            query = query.filter(Program.end_date <= _as_date(end_date_to))

        from app.models.screening import Screening

        film_title = filters.get("filmTitle")
        if film_title:
            query = query.filter(
                Program.screenings.any(Screening.film_title.ilike(f"%{film_title}%"))
            )

        auditorium = filters.get("auditorium")
        if auditorium:
            query = query.filter(
                Program.screenings.any(
                    Screening.auditorium_name.ilike(f"%{auditorium}%")
                )
            )

        programs = query.order_by(Program.start_date.asc(), Program.name.asc()).all()

        return [_serialize_program(program, requester) for program in programs]

    def delete_program(self, program_id, requester):
        """ΛΑ-2.7: only a PROGRAMMER of the program, and only while state == CREATED."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError("Only a PROGRAMMER of this program can delete it")

        if program.state != ProgramState.CREATED:
            raise ConflictError("Program can only be deleted while in CREATED state")

        db.session.delete(program)
        db.session.commit()
        logger.info(
            "Program deleted | program_id=%s | requester_id=%s",
            program_id,
            requester.id,
        )

    def transition_program(self, program_id, target_state, requester):
        """ΛΑ-2.8: only a PROGRAMMER may transition, and only to the single next state
        in the fixed sequence (no rollback, no skipping)."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError(
                "Only a PROGRAMMER of this program can transition its state"
            )

        try:
            target = (
                target_state
                if isinstance(target_state, ProgramState)
                else ProgramState(target_state)
            )
        except (TypeError, ValueError):
            raise ValidationError(f"Unknown target state '{target_state}'")

        current_index = PROGRAM_STATE_ORDER.index(program.state)
        if current_index == len(PROGRAM_STATE_ORDER) - 1:
            raise ConflictError("Program is already in its final state (ANNOUNCED)")

        next_state = PROGRAM_STATE_ORDER[current_index + 1]
        if target != next_state:
            raise ConflictError(
                f"Invalid transition: '{program.state.value}' can only move to "
                f"'{next_state.value}' next (no rollback or skip)"
            )

        if next_state == ProgramState.REVIEW:
            from app.models.screening import Screening, ScreeningState

            unassigned = Screening.query.filter_by(
                program_id=program.id,
                state=ScreeningState.SUBMITTED,
                handler_id=None,
            ).first()
            if unassigned is not None:
                raise ConflictError(
                    "Every SUBMITTED screening must have a handler before REVIEW"
                )

        previous_state = program.state
        program.state = next_state

        if next_state == ProgramState.DECISION:
            for hook in _decision_transition_hooks:
                hook(program)

        db.session.commit()
        logger.info(
            "Program state changed | program_id=%s | from=%s | to=%s | requester_id=%s",
            program.id,
            previous_state.value,
            next_state.value,
            requester.id,
        )
        return program


def _as_date(value):
    if isinstance(value, datetime):
        raise ValidationError("Date must use ISO format YYYY-MM-DD")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValidationError("Date must use ISO format YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{value}' is not a valid ISO date (YYYY-MM-DD)")


def _validate_date_order(start_date, end_date):
    if end_date < start_date:
        raise ValidationError("endDate must be on or after startDate")


def _can_view_program(program, requester):
    return program.state == ProgramState.ANNOUNCED or (
        requester is not None and requester in program.programmers
    )


def _is_insider(program, requester):
    return requester is not None and requester in program.programmers


def _serialize_user(user):
    return {"id": user.id, "username": user.username, "fullName": user.full_name}


def _serialize_program(program, requester):
    """ΛΑ-2.6: public tier for outsiders, full tier (roles + creationDate) for
    PROGRAMMER of this specific program."""
    data = {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "startDate": program.start_date.isoformat(),
        "endDate": program.end_date.isoformat(),
        "state": program.state.value,
    }

    if _is_insider(program, requester):
        data["creationDate"] = program.creation_date.isoformat()
        data["programmers"] = [_serialize_user(u) for u in program.programmers]
        data["staff"] = [_serialize_user(u) for u in program.staff]
    else:
        data["programmerNames"] = [user.full_name for user in program.programmers]

    return data


program_service = ProgramService()
