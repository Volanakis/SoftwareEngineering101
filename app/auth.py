from functools import wraps

from flask import jsonify, session

from app.extensions import db
from app.models.user import User

# ΛΑ-1.3 / ΛΑ-1.4: fallback roles for requests with no program-specific role.
ROLE_VISITOR = "VISITOR"
ROLE_USER = "USER"


def authenticate(username, password):
    """ΛΑ-1.2: verify username/password against the shared user database."""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return None
    return user


def login_user(user):
    session["user_id"] = user.id


def logout_user():
    session.pop("user_id", None)


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    """ΜΛΑ-3.1: reject unauthenticated requests to protected endpoints."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            return jsonify(error="Authentication required"), 401
        return view(*args, **kwargs)

    return wrapped_view


def requires_role(*allowed_roles, role_getter=None):
    """ΜΛΑ-3.2 / ΛΑ-1.8: role-based access control.

    By default the effective role is USER (authenticated, no program-specific
    role) or VISITOR (anonymous). Callers that need a program/screening-scoped
    role (PROGRAMMER, STAFF, SUBMITTER, ...) pass `role_getter(user, *args,
    **kwargs) -> str`, evaluated with the same arguments as the wrapped view.
    """

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()

            if role_getter is not None:
                role = role_getter(user, *args, **kwargs)
            else:
                role = ROLE_USER if user is not None else ROLE_VISITOR

            if role not in allowed_roles:
                return jsonify(error="Insufficient permissions"), 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator
