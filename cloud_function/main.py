import base64
import json
import logging
from datetime import datetime

import functions_framework

from app import create_app
from app.events.click_processor import ClickEventProcessor
from app.extensions import db

logger = logging.getLogger("url_shortener.cloud_function")

_app = create_app()


@functions_framework.cloud_event 
def process_click_event(cloud_event):
    message_data = cloud_event.data["message"]["data"]
    payload = json.loads(base64.b64decode(message_data).decode("utf-8"))

    with _app.app_context():
        processor = ClickEventProcessor(db.session)
        processor.process(
            link_id=payload["link_id"],
            referrer=payload.get("referrer"),
            user_agent=payload.get("user_agent"),
            clicked_at=datetime.fromisoformat(payload["clicked_at"]),
        )
        logger.info("Processed click event for link_id=%s", payload["link_id"])
