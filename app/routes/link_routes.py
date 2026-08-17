from flask import Blueprint, current_app, g, jsonify, request

from app.auth import require_auth
from app.errors import ValidationError
bp = Blueprint("links", __name__, url_prefix="/api/links")


@bp.post("")
@require_auth
def create_link():
    data = request.get_json(silent=True) or {}
    long_url = data.get("long_url")
    if not long_url:
        raise ValidationError("'long_url' is required.")

    link_service = current_app.extensions["link_service"]
    link = link_service.create_link(
        owner=g.current_user,
        long_url=long_url,
        custom_code=data.get("custom_code"),
    )
    return jsonify(_serialize_link(link)), 201


@bp.get("")
@require_auth
def list_links():
    link_service = current_app.extensions["link_service"]
    links = link_service.list_links_for_user(g.current_user)
    return jsonify([_serialize_link(link) for link in links])


@bp.delete("/<int:link_id>")
@require_auth
def deactivate_link(link_id):
    link_service = current_app.extensions["link_service"]
    link = link_service.deactivate_link(g.current_user, link_id)
    return jsonify(_serialize_link(link))


def _serialize_link(link):
    return {
        "id": link.id,
        "code": link.code,
        "short_url": f"{current_app.config['BASE_URL']}/{link.code}",
        "long_url": link.long_url,
        "is_active": link.is_active,
        "click_count": link.click_count,
        "created_at": link.created_at.isoformat(),
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
    }
