from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    api_token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    links = db.relationship("ShortLink", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


class ShortLink(db.Model):
    __tablename__ = "short_links"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    long_url = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", back_populates="links")
    click_events = db.relationship(
        "ClickEvent", back_populates="link", cascade="all, delete-orphan"
    )

    def is_expired(self, now=None):
        if self.expires_at is None:
            return False
        return (now or datetime.utcnow()) >= self.expires_at

    def __repr__(self):
        return f"<ShortLink id={self.id} code={self.code!r}>"


class ClickEvent(db.Model):
    __tablename__ = "click_events"

    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey("short_links.id"), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    referrer_domain = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    browser = db.Column(db.String(20), nullable=True)

    link = db.relationship("ShortLink", back_populates="click_events")

    def __repr__(self):
        return f"<ClickEvent id={self.id} link_id={self.link_id}>"
