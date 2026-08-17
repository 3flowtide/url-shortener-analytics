from flask import Blueprint, jsonify, request

from app.services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
_auth_service = AuthService()


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    user, token = _auth_service.register(data.get("email", ""), data.get("password", ""))
    return jsonify({"email": user.email, "api_token": token}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user, token = _auth_service.login(data.get("email", ""), data.get("password", ""))
    return jsonify({"email": user.email, "api_token": token})
