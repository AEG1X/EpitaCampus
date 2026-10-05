from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

COOKIE_NAME = "campus_session"
password_hash = PasswordHash.recommended()


def create_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.token_days)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.secret_key, algorithm="HS256")


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
    if user is None:
        raise unauthorized
    return user
