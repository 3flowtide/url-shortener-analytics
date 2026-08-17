from functools import wraps

from flask import g, request

from app.services.auth_service import AuthService

_auth_service = AuthService()


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else None
        g.current_user = _auth_service.authenticate_by_token(token)
        return view(*args, **kwargs)

    return wrapped
