from datetime import date

from app.extensions import db
from app.models.program import Program, ProgramRole, RoleType
from app.services.errors import ConflictError, ValidationError

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


def _as_date(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


program_service = ProgramService()
