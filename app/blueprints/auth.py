from flask import Blueprint, jsonify, request

from app.auth import authenticate, login_user, logout_user
from app.extensions import limiter


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON object is required"), 400

    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not username.strip() or not isinstance(password, str):
        return jsonify(error="username and password are required"), 400

    user = authenticate(username.strip(), password)
    if user is None:
        return jsonify(error="Invalid username or password"), 401

    login_user(user)
    return jsonify(id=user.id, username=user.username, fullName=user.full_name), 200


@auth_bp.post("/logout")
def logout():
    logout_user()
    return "", 204
