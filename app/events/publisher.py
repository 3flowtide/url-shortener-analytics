import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime

logger = logging.getLogger("url_shortener.events")


@dataclass
class ClickEventPayload:
    link_id: int
    referrer: str | None
    user_agent: str | None
    clicked_at: str  # date as text


class EventPublisher(ABC):
    @abstractmethod
    def publish_click_event(self, payload):
        raise NotImplementedError


class LocalEventPublisher(EventPublisher):
    def __init__(self, processor):
        self._processor = processor

    def publish_click_event(self, payload):
        try:
            self._processor.process(
                link_id=payload.link_id,
                referrer=payload.referrer,
                user_agent=payload.user_agent,
                clicked_at=datetime.fromisoformat(payload.clicked_at),
            )
        except Exception:
            logger.exception("Failed to process click event for link_id=%s", payload.link_id)


class PubSubEventPublisher(EventPublisher):
    def __init__(self, project_id, topic):
        from google.cloud import pubsub_v1  # lazy import

        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(project_id, topic)

    def publish_click_event(self, payload):
        data = json.dumps(asdict(payload)).encode("utf-8")
        future = self._publisher.publish(self._topic_path, data)
        future.add_done_callback(self._log_publish_result)  # no wait

    @staticmethod
    def _log_publish_result(future):
        try:
            future.result()
        except Exception:
            logger.exception("Failed to publish click event to Pub/Sub")
