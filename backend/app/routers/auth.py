from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import COOKIE_NAME, create_token, current_user, password_hash
from ..config import settings
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool


def set_session(response: Response, user: User) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id),
        max_age=settings.token_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    """Indique au frontend si l'inscription est ouverte (toujours vrai tant qu'il n'y a aucun compte)."""
    has_users = db.scalar(select(func.count(User.id))) > 0
    return {"signup_open": settings.allow_signup or not has_users, "first_user": not has_users}


@router.post("/signup", response_model=UserOut)
def signup(body: SignupIn, response: Response, db: Session = Depends(get_db)):
    first_user = db.scalar(select(func.count(User.id))) == 0
    if not (first_user or settings.allow_signup):
        raise HTTPException(403, "Les inscriptions sont fermées")
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Un compte existe déjà avec cet e-mail")
    user = User(
        email=body.email.lower(),
        name=body.name,
        password_hash=password_hash.hash(body.password),
        is_admin=first_user,
    )
    db.add(user)
    db.commit()
    set_session(response, user)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not password_hash.verify(body.password, user.password_hash):
        raise HTTPException(401, "E-mail ou mot de passe incorrect")
    set_session(response, user)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
