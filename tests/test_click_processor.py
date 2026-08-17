import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app
from app.config import Config
from app.events.click_processor import ClickEventProcessor
from app.extensions import db
from app.models import ClickEvent, ShortLink, User


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PUBSUB_ENABLED = False


@pytest.fixture
def app_context():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def link(app_context):
    owner = User(email="owner@example.com", password_hash="x", api_token_hash="y")
    db.session.add(owner)
    db.session.commit()

    short_link = ShortLink(code="abc123", long_url="https://example.com", owner_id=owner.id)
    db.session.add(short_link)
    db.session.commit()
    return short_link


@pytest.fixture
def processor(app_context):
    return ClickEventProcessor(db.session)


def test_process_increments_click_count_and_records_an_event(processor, link):
    processor.process(
        link_id=link.id,
        referrer="https://google.com/search",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    )

    assert link.click_count == 1
    events = ClickEvent.query.filter_by(link_id=link.id).all()
    assert len(events) == 1
    assert events[0].referrer_domain == "google.com"
    assert events[0].device_type == "mobile"


def test_process_silently_ignores_unknown_link_id(processor, app_context):
    processor.process(link_id=999999, referrer=None, user_agent=None)

    assert ClickEvent.query.count() == 0


@pytest.mark.parametrize(
    "user_agent,expected",
    [
        (None, "unknown"),
        ("Mozilla/5.0 (iPad; CPU OS 17_0)", "tablet"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)", "mobile"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "desktop"),
    ],
)
def test_classify_device(user_agent, expected):
    assert ClickEventProcessor._classify_device(user_agent) == expected


@pytest.mark.parametrize(
    "user_agent,expected",
    [
        (None, "unknown"),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "edge",
        ),
        ("Mozilla/5.0 Chrome/120.0 Safari/537.36", "chrome"),
        ("Mozilla/5.0 Firefox/120.0", "firefox"),
        ("Mozilla/5.0 (compatible; SomeBot/1.0)", "other"),
    ],
)
def test_classify_browser(user_agent, expected):
    assert ClickEventProcessor._classify_browser(user_agent) == expected


def test_extract_domain_handles_missing_and_relative_referrers():
    assert ClickEventProcessor._extract_domain(None) is None
    assert ClickEventProcessor._extract_domain("") is None
    assert (
        ClickEventProcessor._extract_domain("https://news.ycombinator.com/item?id=1")
        == "news.ycombinator.com"
    )
