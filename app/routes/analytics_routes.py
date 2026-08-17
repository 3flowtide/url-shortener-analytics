from flask import Blueprint, current_app, g, jsonify

from app.auth import require_auth

bp = Blueprint("analytics", __name__, url_prefix="/api/links")


@bp.get("/<int:link_id>/analytics")
@require_auth
def get_analytics(link_id):
    analytics_service = current_app.extensions["analytics_service"]
    return jsonify(analytics_service.get_link_analytics(g.current_user, link_id))
