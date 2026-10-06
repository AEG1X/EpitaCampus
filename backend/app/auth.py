import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

COOKIE_NAME = "campus_session"
password_hash = PasswordHash.recommended()
# Haché factice pour que la vérification prenne le même temps quand l'e-mail n'existe pas.
DUMMY_HASH = password_hash.hash("mot-de-passe-factice")


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.token_days)
    payload = {"sub": str(user.id), "ver": user.session_version, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def current_user(
    db: Session = Depends(get_db), token: str | None = Cookie(default=None, alias=COOKIE_NAME)
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Non connecté")
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise unauthorized
    user = db.get(User, int(payload["sub"]))
    if user is None or payload.get("ver", 0) != user.session_version:
        raise unauthorized
    return user


class LoginLimiter:
    """Bloque une adresse IP après trop d'échecs de connexion (protection contre le brute force)."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 15 * 60):
        self.max_failures = max_failures
        self.window = window_seconds
        self.failures: dict[str, deque] = defaultdict(deque)

    @staticmethod
    def key(request: Request) -> str:
        # Caddy transmet l'adresse réelle du client dans X-Forwarded-For.
        forwarded = request.headers.get("x-forwarded-for")
        return forwarded.split(",")[0].strip() if forwarded else request.client.host

    def _recent(self, key: str) -> deque:
        attempts = self.failures[key]
        while attempts and attempts[0] < time.monotonic() - self.window:
            attempts.popleft()
        return attempts

    def check(self, request: Request) -> None:
        if len(self._recent(self.key(request))) >= self.max_failures:
            raise HTTPException(429, "Trop de tentatives, réessaie dans 15 minutes")

    def fail(self, request: Request) -> None:
        self._recent(self.key(request)).append(time.monotonic())

    def reset(self, request: Request) -> None:
        self.failures.pop(self.key(request), None)


login_limiter = LoginLimiter()
