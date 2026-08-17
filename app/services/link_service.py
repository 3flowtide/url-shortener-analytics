from urllib.parse import urlparse

from app.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import ShortLink

MAX_CODE_GENERATION_ATTEMPTS = 5


class LinkService:
    def __init__(self, code_generator):
        self._code_generator = code_generator

    def create_link(self, owner, long_url, custom_code=None, expires_at=None):
        self._validate_long_url(long_url)

        code = self._resolve_code(custom_code)

        link = ShortLink(
            code=code,
            long_url=long_url,
            owner_id=owner.id,
            expires_at=expires_at,
        )
        db.session.add(link)
        db.session.commit()
        return link

    def get_active_link_by_code(self, code):
        link = ShortLink.query.filter_by(code=code).first()
        if link is None or not link.is_active:
            raise NotFoundError(f"No active short link found for code '{code}'.")
        if link.is_expired():
            raise NotFoundError(f"Short link '{code}' has expired.")
        return link

    def list_links_for_user(self, user):
        links = ShortLink.query.filter_by(owner_id=user.id).order_by(ShortLink.created_at.desc())
        return links.all()

    def get_owned_link(self, user, link_id):
        link = db.session.get(ShortLink, link_id)
        if link is None:
            raise NotFoundError(f"Short link {link_id} does not exist.")
        if link.owner_id != user.id:
            raise AuthorizationError("You do not own this short link.")
        return link

    def deactivate_link(self, user, link_id):
        link = self.get_owned_link(user, link_id)
        link.is_active = False
        db.session.commit()
        return link

    def _resolve_code(self, custom_code):
        if custom_code:
            self._validate_custom_code(custom_code)
            if ShortLink.query.filter_by(code=custom_code).first() is not None:
                raise ConflictError(f"Short code '{custom_code}' is already taken.")
            return custom_code

        for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
            candidate = self._code_generator.generate()
            if ShortLink.query.filter_by(code=candidate).first() is None:
                return candidate

        raise ConflictError("Could not generate a unique short code, please retry.")

    @staticmethod
    def _validate_long_url(long_url):
        parsed = urlparse(long_url or "")
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError(
                f"'{long_url}' is not a valid http(s) URL."
            )

    @staticmethod
    def _validate_custom_code(custom_code):
        if not custom_code.isalnum() or not (3 <= len(custom_code) <= 32):
            raise ValidationError(
                "Custom short codes must be 3-32 alphanumeric characters."
            )
