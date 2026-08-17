from datetime import datetime

from flask import Blueprint, current_app, redirect, render_template, request

from app.events.publisher import ClickEventPayload

bp = Blueprint("redirect", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/<code>")
def redirect_to_long_url(code):
    link_service = current_app.extensions["link_service"]
    link = link_service.get_active_link_by_code(code)

    event_publisher = current_app.extensions["event_publisher"]
    event_publisher.publish_click_event(
        ClickEventPayload(
            link_id=link.id,
            referrer=request.referrer,
            user_agent=request.headers.get("User-Agent"),
            clicked_at=datetime.utcnow().isoformat(),
        )
    )

    return redirect(link.long_url, code=302)
