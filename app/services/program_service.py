from datetime import date

from app.extensions import db
from app.models.program import Program, ProgramRole, ProgramState, RoleType
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


def _as_date(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


program_service = ProgramService()
