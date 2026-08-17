import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
    SHORT_CODE_LENGTH = int(os.environ.get("SHORT_CODE_LENGTH", "7"))

    PUBSUB_ENABLED = os.environ.get("PUBSUB_ENABLED", "false").lower() == "true"
    PUBSUB_PROJECT_ID = os.environ.get("PUBSUB_PROJECT_ID", "")
    PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "click-events")
