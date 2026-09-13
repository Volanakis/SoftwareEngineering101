from flask import Blueprint, jsonify, request
from app.extensions import limiter

from app.auth import get_current_user
from app.services.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.services.program_service import program_service

programs_bp = Blueprint("programs", __name__, url_prefix="/programs")


def _json_object():
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


@programs_bp.errorhandler(ValidationError)
def _handle_validation_error(error):
    return jsonify(error=str(error)), 400


@programs_bp.errorhandler(AuthorizationError)
def _handle_authorization_error(error):
    return jsonify(error=str(error)), 403


@programs_bp.errorhandler(NotFoundError)
def _handle_not_found_error(error):
    return jsonify(error=str(error)), 404


@programs_bp.errorhandler(ConflictError)
def _handle_conflict_error(error):
    return jsonify(error=str(error)), 409


@programs_bp.post("")
def create_program():
    """ΛΑ-2.1, sequence 11."""
    user = get_current_user()
    if user is None:
        return jsonify(error="Authentication required"), 401

    payload = _json_object()
    program = program_service.create_program(payload, user)
    return jsonify(program_service.get_program(program.id, user)), 201


@programs_bp.get("")
@limiter.limit("30 per minute")
def search_programs():
    """ΛΑ-2.5, activity 09."""
    results = program_service.search_programs(request.args.to_dict(), get_current_user())
    return jsonify(results=results), 200


@programs_bp.get("/<program_id>")
def get_program(program_id):
    """ΛΑ-2.6, sequence 14."""
    dto = program_service.get_program(program_id, get_current_user())
    return jsonify(dto), 200


@programs_bp.put("/<program_id>")
def update_program(program_id):
    """ΛΑ-2.2, sequence 13."""
    user = get_current_user()
    payload = _json_object()
    program = program_service.update_program(program_id, payload, user)
    return jsonify(program_service.get_program(program.id, user)), 200


@programs_bp.delete("/<program_id>")
def delete_program(program_id):
    """ΛΑ-2.7, sequence 15."""
    program_service.delete_program(program_id, get_current_user())
    return "", 204


@programs_bp.post("/<program_id>/roles")
def add_role(program_id):
    """ΛΑ-2.3 / ΛΑ-2.4, sequence 12."""
    user = get_current_user()
    payload = _json_object()
    user_id = payload.get("userId")
    role_type = payload.get("roleType")

    if not user_id or role_type not in ("PROGRAMMER", "STAFF"):
        return jsonify(error="userId and a valid roleType (PROGRAMMER|STAFF) are required"), 400

    if role_type == "PROGRAMMER":
        program = program_service.add_programmer(program_id, user_id, user)
    else:
        program = program_service.add_staff(program_id, user_id, user)

    return jsonify(program_service.get_program(program.id, user)), 200


@programs_bp.delete("/<program_id>/roles/<user_id>")
def remove_role(program_id, user_id):
    """Remove a PROGRAMMER/STAFF assignment without removing the creator."""
    program_service.remove_role(program_id, user_id, get_current_user())
    return "", 204


@programs_bp.post("/<program_id>/transitions")
def transition_program(program_id):
    """ΛΑ-2.8, activity 06."""
    user = get_current_user()
    payload = _json_object()
    target_state = payload.get("targetState")

    if not target_state:
        return jsonify(error="targetState is required"), 400

    program = program_service.transition_program(program_id, target_state, user)
    return jsonify(program_service.get_program(program.id, user)), 200
