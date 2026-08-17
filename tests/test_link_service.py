import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app
from app.config import Config
from app.errors import AuthorizationError, ConflictError, ValidationError
from app.extensions import db
from app.models import User
from app.services.link_service import LinkService
from app.services.short_code_generator import ShortCodeGenerator


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
def user(app_context):
    user = User(email="test@example.com", password_hash="x", api_token_hash="y")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def link_service():
    return LinkService(ShortCodeGenerator(length=6))


def test_create_link_generates_code(link_service, user):
    link = link_service.create_link(owner=user, long_url="https://example.com/page")
    assert len(link.code) == 6
    assert link.long_url == "https://example.com/page"
    assert link.is_active is True


def test_create_link_rejects_invalid_url(link_service, user):
    with pytest.raises(ValidationError):
        link_service.create_link(owner=user, long_url="not-a-url")


def test_create_link_with_taken_custom_code_conflicts(link_service, user):
    link_service.create_link(owner=user, long_url="https://a.com", custom_code="mycode")
    with pytest.raises(ConflictError):
        link_service.create_link(owner=user, long_url="https://b.com", custom_code="mycode")


def test_deactivate_link_requires_ownership(link_service, user, app_context):
    other_user = User(email="other@example.com", password_hash="x", api_token_hash="z")
    db.session.add(other_user)
    db.session.commit()

    link = link_service.create_link(owner=user, long_url="https://example.com")

    with pytest.raises(AuthorizationError):
        link_service.deactivate_link(other_user, link.id)


def test_get_active_link_by_code_round_trips(link_service, user):
    link = link_service.create_link(owner=user, long_url="https://example.com/x")
    fetched = link_service.get_active_link_by_code(link.code)
    assert fetched.id == link.id
