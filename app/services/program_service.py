from datetime import date

from app.extensions import db
from app.models.program import Program, ProgramRole, ProgramState, RoleType
from app.models.user import User
from app.services.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError

REQUIRED_CREATE_FIELDS = ("name", "description", "startDate", "endDate")


class ProgramService:
    def create_program(self, data, creator):
        """ΛΑ-2.1: create a program; the creator is auto-registered as PROGRAMMER."""
        missing = [field for field in REQUIRED_CREATE_FIELDS if not data.get(field)]
        if missing:
            raise ValidationError(f"Missing required field(s): {', '.join(missing)}")

        name = data["name"]
        if Program.query.filter_by(name=name).first() is not None:
            raise ConflictError(f"Program name '{name}' is already taken")

        program = Program(
            name=name,
            description=data["description"],
            start_date=_as_date(data["startDate"]),
            end_date=_as_date(data["endDate"]),
        )
        db.session.add(program)
        db.session.flush()

        db.session.add(ProgramRole(program=program, user=creator, role_type=RoleType.PROGRAMMER))
        db.session.commit()

        return program

    def update_program(self, program_id, data, requester):
        """ΛΑ-2.2: update name/description/dates. Only a PROGRAMMER of this program may
        update it, and only before it reaches ANNOUNCED. PROGRAMMERS/STAFF set changes go
        through add_programmer/add_staff (ΛΑ-2.3/2.4) instead of this method, so the
        creator can never be dropped here (ΛΑ-2.2.3)."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        if requester not in program.programmers:
            raise AuthorizationError("Only a PROGRAMMER of this program can update it")

        if program.state == ProgramState.ANNOUNCED:
            raise ConflictError("Program is ANNOUNCED and can no longer be updated")

        if "name" in data:
            new_name = data["name"]
            if not new_name:
                raise ValidationError("name cannot be empty")
            if (
                new_name != program.name
                and Program.query.filter_by(name=new_name).first() is not None
            ):
                raise ConflictError(f"Program name '{new_name}' is already taken")
            program.name = new_name

        if "description" in data:
            if not data["description"]:
                raise ValidationError("description cannot be empty")
            program.description = data["description"]

        if "startDate" in data:
            program.start_date = _as_date(data["startDate"])

        if "endDate" in data:
            program.end_date = _as_date(data["endDate"])

        db.session.commit()
        return program

    def add_programmer(self, program_id, user_id, requester):
        """ΛΑ-2.3: add a PROGRAMMER; the user must not already hold a role in this program."""
        program, user = self._require_programmer_and_target_user(program_id, user_id, requester)
        self._ensure_user_has_no_role(program, user)

        db.session.add(ProgramRole(program=program, user=user, role_type=RoleType.PROGRAMMER))
        db.session.commit()
        return program

    def add_staff(self, program_id, user_id, requester):
        """ΛΑ-2.4: add STAFF; frozen once the program leaves CREATED (enters SUBMISSION+)."""
        program, user = self._require_programmer_and_target_user(program_id, user_id, requester)

        if program.state != ProgramState.CREATED:
            raise ConflictError("STAFF set is frozen once the program leaves CREATED")

        self._ensure_user_has_no_role(program, user)

        db.session.add(ProgramRole(program=program, user=user, role_type=RoleType.STAFF))
        db.session.commit()
        return program

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

    def get_program(self, program_id, requester):
        """ΛΑ-2.6: view a program, redacted per the requester's role."""
        program = db.session.get(Program, program_id)
        if program is None:
            raise NotFoundError(f"Program '{program_id}' not found")

        return _serialize_program(program, requester)

    def search_programs(self, filters, requester):
        """ΛΑ-2.5: AND-combined filters, redacted per role, sorted by date then name.

        `filmTitle`/`auditorium` filters from API_CONTRACT.md depend on the Screening
        model (Person B) and are not applied yet; they are accepted but ignored here.
        """
        query = Program.query

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

        programs = query.order_by(Program.start_date.asc(), Program.name.asc()).all()

        return [_serialize_program(program, requester) for program in programs]


def _as_date(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


def _is_insider(program, requester):
    return requester is not None and (
        requester in program.programmers or requester in program.staff
    )


def _serialize_user(user):
    return {"id": user.id, "username": user.username, "fullName": user.full_name}


def _serialize_program(program, requester):
    """ΛΑ-2.6: public tier for outsiders, full tier (roles + creationDate) for
    PROGRAMMER/STAFF of this specific program."""
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

    return data


program_service = ProgramService()
