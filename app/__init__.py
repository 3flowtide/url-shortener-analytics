import logging

from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()

from app.config import Config
from app.errors import ApplicationError
from app.events.click_processor import ClickEventProcessor
from app.events.publisher import LocalEventPublisher, PubSubEventPublisher
from app.extensions import db
from app.services.analytics_service import AnalyticsService
from app.services.link_service import LinkService
from app.services.short_code_generator import ShortCodeGenerator

logger = logging.getLogger("url_shortener")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    code_generator = ShortCodeGenerator(length=app.config["SHORT_CODE_LENGTH"])
    link_service = LinkService(code_generator)
    analytics_service = AnalyticsService(link_service)

    app.extensions["link_service"] = link_service
    app.extensions["analytics_service"] = analytics_service
    app.extensions["event_publisher"] = _build_event_publisher(app)

    from app.routes import register_blueprints

    register_blueprints(app)

    @app.errorhandler(ApplicationError)
    def handle_application_error(err):
        return (
            jsonify({"error": err.__class__.__name__, "detail": err.message}),
            err.status_code,
        )

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            # avoid startup crash
            logger.exception("db.create_all() failed at startup; continuing anyway")

    return app


def _build_event_publisher(app):
    if app.config["PUBSUB_ENABLED"]:
        logger.info("Publishing click events to Pub/Sub topic '%s'", app.config["PUBSUB_TOPIC"])
        return PubSubEventPublisher(
            project_id=app.config["PUBSUB_PROJECT_ID"],
            topic=app.config["PUBSUB_TOPIC"],
        )

    logger.info("PUBSUB_ENABLED is false; processing click events in-process.")
    return LocalEventPublisher(ClickEventProcessor(db.session))
