from datetime import datetime
from urllib.parse import urlparse

from app.models import ClickEvent, ShortLink

MOBILE_MARKERS = ("Mobile", "iPhone", "Android")
TABLET_MARKERS = ("iPad", "Tablet")
BROWSER_MARKERS = ("Edg", "Chrome", "Firefox", "Safari")


class ClickEventProcessor:
    def __init__(self, session):
        self._session = session

    def process(self, link_id, referrer, user_agent, clicked_at=None):
        link = self._session.get(ShortLink, link_id)
        if link is None:
            return

        event = ClickEvent(
            link_id=link_id,
            clicked_at=clicked_at or datetime.utcnow(),
            referrer_domain=self._extract_domain(referrer),
            device_type=self._classify_device(user_agent),
            browser=self._classify_browser(user_agent),
        )
        link.click_count += 1

        self._session.add(event)
        self._session.commit()

    @staticmethod
    def _extract_domain(referrer):
        if not referrer:
            return None
        domain = urlparse(referrer).netloc
        return domain or None

    @staticmethod
    def _classify_device(user_agent):
        if not user_agent:
            return "unknown"

        for marker in TABLET_MARKERS:
            if marker in user_agent:
                return "tablet"

        for marker in MOBILE_MARKERS:
            if marker in user_agent:
                return "mobile"

        return "desktop"

    @staticmethod
    def _classify_browser(user_agent):
        if not user_agent:
            return "unknown"
        for marker in BROWSER_MARKERS:
            if marker in user_agent:
                return "edge" if marker == "Edg" else marker.lower()
        return "other"
