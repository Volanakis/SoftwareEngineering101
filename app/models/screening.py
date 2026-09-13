import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db


class ScreeningState(enum.Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    REJECTED = "REJECTED"


class Screening(db.Model):
    __tablename__ = "screenings"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    creation_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    state = db.Column(
        db.Enum(ScreeningState),
        default=ScreeningState.CREATED,
        nullable=False,
    )

    program_id = db.Column(
        db.String(36),
        db.ForeignKey("programs.id"),
        nullable=False,
    )

    submitter_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    handler_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    film_title = db.Column(
        db.String(255),
        nullable=False,
    )

    film_cast = db.Column(
        db.Text,
        nullable=True,
    )

    film_genres = db.Column(
        db.Text,
        nullable=True,
    )

    film_duration_minutes = db.Column(
        db.Integer,
        nullable=True,
    )

    auditorium_name = db.Column(
        db.String(255),
        nullable=True,
    )

    start_time = db.Column(
        db.DateTime,
        nullable=True,
    )

    end_time = db.Column(
        db.DateTime,
        nullable=True,
    )

    review_score = db.Column(
        db.Float,
        nullable=True,
    )

    review_comments = db.Column(
        db.Text,
        nullable=True,
    )

    rejection_reason = db.Column(
        db.Text,
        nullable=True,
    )

    final_submitted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    approval_notes = db.Column(
        db.Text,
        nullable=True,
    )

    program = db.relationship(
        "Program",
        back_populates="screenings",
    )

    submitter = db.relationship(
        "User",
        foreign_keys=[submitter_id],
        backref="submitted_screenings",
    )

    handler = db.relationship(
        "User",
        foreign_keys=[handler_id],
        backref="handled_screenings",
    )

    def __repr__(self):
        return f"<Screening {self.film_title} state={self.state.value}>"
