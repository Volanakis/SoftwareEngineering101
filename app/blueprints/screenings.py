from flask import Blueprint, jsonify, request
from app.extensions import limiter

from app.auth import get_current_user
from app.services.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.screening_service import screening_service


screenings_bp = Blueprint(
    "screenings",
    __name__,
    url_prefix="/programs/<program_id>/screenings",
)


def _json_object():
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


@screenings_bp.errorhandler(ValidationError)
def _handle_validation_error(error):
    return jsonify(error=str(error)), 400


@screenings_bp.errorhandler(AuthorizationError)
def _handle_authorization_error(error):
    return jsonify(error=str(error)), 403


@screenings_bp.errorhandler(NotFoundError)
def _handle_not_found_error(error):
    return jsonify(error=str(error)), 404


@screenings_bp.errorhandler(ConflictError)
def _handle_conflict_error(error):
    return jsonify(error=str(error)), 409


def _serialize_screening(screening):
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
        "submitterId": screening.submitter_id,
        "handlerId": screening.handler_id,
        "reviewScore": screening.review_score,
        "reviewComments": screening.review_comments,
        "rejectionReason": screening.rejection_reason,
        "finalSubmitted": screening.final_submitted,
        "approvalNotes": screening.approval_notes,
    }


@screenings_bp.post("")
def create_screening(program_id):
    user = get_current_user()

    if user is None:
        return jsonify(
            error="Authentication required"
        ), 401

    payload = _json_object()

    screening = screening_service.create_screening(
        program_id,
        payload,
        user,
    )

    return jsonify(
        _serialize_screening(screening)
    ), 201


@screenings_bp.get("")
@limiter.limit("30 per minute")
def search_screenings(program_id):
    results = screening_service.search_screenings(
        program_id,
        request.args.to_dict(),
        get_current_user(),
    )

    return jsonify(
        results=results
    ), 200


@screenings_bp.get("/<screening_id>")
def get_screening(
    program_id,
    screening_id,
):
    result = screening_service.get_screening(
        program_id,
        screening_id,
        get_current_user(),
    )

    return jsonify(result), 200


@screenings_bp.put("/<screening_id>")
def update_screening(
    program_id,
    screening_id,
):
    payload = _json_object()

    screening = screening_service.update_screening(
        program_id,
        screening_id,
        payload,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/submit")
@limiter.limit("10 per minute")
def submit_screening(
    program_id,
    screening_id,
):
    screening = screening_service.submit_screening(
        program_id,
        screening_id,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.delete("/<screening_id>")
def withdraw_screening(
    program_id,
    screening_id,
):
    screening_service.withdraw_screening(
        program_id,
        screening_id,
        get_current_user(),
    )

    return "", 204


@screenings_bp.post("/<screening_id>/handler")
def assign_handler(
    program_id,
    screening_id,
):
    payload = _json_object()

    user_id = payload.get("userId")

    if not user_id:
        return jsonify(
            error="userId is required"
        ), 400

    screening = screening_service.assign_handler(
        program_id,
        screening_id,
        user_id,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/review")
def review_screening(
    program_id,
    screening_id,
):
    payload = _json_object()

    screening = screening_service.review_screening(
        program_id,
        screening_id,
        payload,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/approve")
def approve_screening(
    program_id,
    screening_id,
):
    payload = _json_object()

    screening = screening_service.approve_screening(
        program_id,
        screening_id,
        payload,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/reject")
def reject_screening(
    program_id,
    screening_id,
):
    payload = _json_object()

    screening = screening_service.reject_screening(
        program_id,
        screening_id,
        payload,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/final-submit")
@limiter.limit("10 per minute")
def final_submit_screening(
    program_id,
    screening_id,
):
    payload = _json_object()

    screening = screening_service.final_submit_screening(
        program_id,
        screening_id,
        payload,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200


@screenings_bp.post("/<screening_id>/accept")
def accept_screening(
    program_id,
    screening_id,
):
    screening = screening_service.accept_screening(
        program_id,
        screening_id,
        get_current_user(),
    )

    return jsonify(
        _serialize_screening(screening)
    ), 200
