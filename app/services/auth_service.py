import hashlib
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import AuthenticationError, ConflictError, ValidationError
from app.extensions import db
from app.models import User


class AuthService:
    def register(self, email, password):
        email = self._validate_email(email)
        self._validate_password(password)

        if User.query.filter_by(email=email).first() is not None:
            raise ConflictError(f"An account with email '{email}' already exists.")

        raw_token = self._generate_token()
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            api_token_hash=self._hash_token(raw_token),
        )
        db.session.add(user)
        db.session.commit()
        return user, raw_token

    def login(self, email, password):
        email = self._validate_email(email)
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, password):
            raise AuthenticationError("Invalid email or password.")

        raw_token = self._generate_token()
        user.api_token_hash = self._hash_token(raw_token)
        db.session.commit()
        return user, raw_token

    def authenticate_by_token(self, raw_token):
        if not raw_token:
            raise AuthenticationError("Missing bearer token.")

        user = User.query.filter_by(api_token_hash=self._hash_token(raw_token)).first()
        if user is None:
            raise AuthenticationError("Invalid or expired token.")

        return user

    @staticmethod
    def _generate_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def _hash_token(raw_token):
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_email(email):
        email = (email or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError(f"'{email}' is not a valid email address.")
        return email

    @staticmethod
    def _validate_password(password):
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
