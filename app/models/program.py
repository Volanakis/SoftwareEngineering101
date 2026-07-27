import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db


class ProgramState(enum.Enum):
    CREATED = "CREATED"
    SUBMISSION = "SUBMISSION"
    ASSIGNMENT = "ASSIGNMENT"
    REVIEW = "REVIEW"
    SCHEDULING = "SCHEDULING"
    FINAL_SUBMISSION = "FINAL_SUBMISSION"
    DECISION = "DECISION"
    ANNOUNCED = "ANNOUNCED"


class RoleType(enum.Enum):
    PROGRAMMER = "PROGRAMMER"
    STAFF = "STAFF"


class Program(db.Model):
    __tablename__ = "programs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    creation_date = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    state = db.Column(db.Enum(ProgramState), default=ProgramState.CREATED, nullable=False)

    roles = db.relationship(
        "ProgramRole", back_populates="program", cascade="all, delete-orphan"
    )

    @property
    def programmers(self):
        return [role.user for role in self.roles if role.role_type == RoleType.PROGRAMMER]

    @property
    def staff(self):
        return [role.user for role in self.roles if role.role_type == RoleType.STAFF]

    def __repr__(self):
        return f"<Program {self.name}>"


class ProgramRole(db.Model):
    """Association between User and Program (ΛΑ-1.5: at most one role per program per user)."""

    __tablename__ = "program_roles"
    __table_args__ = (
        db.UniqueConstraint("program_id", "user_id", name="uq_program_roles_program_user"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_type = db.Column(db.Enum(RoleType), nullable=False)
    program_id = db.Column(db.String(36), db.ForeignKey("programs.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    program = db.relationship("Program", back_populates="roles")
    user = db.relationship("User", back_populates="program_roles")

    def __repr__(self):
        return f"<ProgramRole {self.role_type.value} user={self.user_id} program={self.program_id}>"
