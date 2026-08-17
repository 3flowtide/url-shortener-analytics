import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app
from app.config import Config
from app.errors import AuthenticationError, ConflictError, ValidationError
from app.extensions import db
from app.services.auth_service import AuthService


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
def auth_service():
    return AuthService()


def test_register_hashes_password_and_returns_a_raw_token(auth_service, app_context):
    user, raw_token = auth_service.register("new@example.com", "correcthorse")

    assert user.password_hash != "correcthorse"
    assert user.api_token_hash != raw_token


def test_register_rejects_duplicate_email(auth_service, app_context):
    auth_service.register("dup@example.com", "correcthorse")

    with pytest.raises(ConflictError):
        auth_service.register("dup@example.com", "correcthorse")


def test_register_rejects_invalid_email(auth_service, app_context):
    with pytest.raises(ValidationError):
        auth_service.register("not-an-email", "correcthorse")


def test_register_rejects_short_password(auth_service, app_context):
    with pytest.raises(ValidationError):
        auth_service.register("short@example.com", "abc123")


def test_login_succeeds_and_rotates_the_token(auth_service, app_context):
    _, first_token = auth_service.register("rotate@example.com", "correcthorse")

    _, second_token = auth_service.login("rotate@example.com", "correcthorse")

    assert second_token != first_token
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_by_token(first_token)
    assert auth_service.authenticate_by_token(second_token).email == "rotate@example.com"


def test_login_rejects_wrong_password(auth_service, app_context):
    auth_service.register("wrongpw@example.com", "correcthorse")

    with pytest.raises(AuthenticationError):
        auth_service.login("wrongpw@example.com", "not-the-password")


def test_login_rejects_unknown_email_with_same_error_as_wrong_password(auth_service, app_context):
    with pytest.raises(AuthenticationError):
        auth_service.login("nobody@example.com", "correcthorse")


def test_authenticate_by_token_rejects_missing_token(auth_service, app_context):
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_by_token(None)


def test_authenticate_by_token_rejects_unknown_token(auth_service, app_context):
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_by_token("not-a-real-token")
