import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Grade, User

router = APIRouter(prefix="/api/grades", tags=["grades"])


class GradeIn(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    value: float = Field(ge=0)
    max_value: float = Field(default=20, gt=0)
    coefficient: float = Field(default=1, gt=0)
    date: dt.date

    @model_validator(mode="after")
    def value_le_max(self):
        if self.value > self.max_value:
            raise ValueError("La note dépasse le barème")
        return self


class GradeOut(GradeIn):
    id: int


@router.get("", response_model=list[GradeOut])
def list_grades(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Grade).where(Grade.user_id == user.id).order_by(Grade.date)).all()


@router.post("", response_model=GradeOut)
def add_grade(body: GradeIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    grade = Grade(user_id=user.id, **body.model_dump())
    db.add(grade)
    db.commit()
    return grade


def get_grade(db: Session, user: User, grade_id: int) -> Grade:
    grade = db.get(Grade, grade_id)
    if grade is None or grade.user_id != user.id:
        raise HTTPException(404, "Note introuvable")
    return grade


@router.put("/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int, body: GradeIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    grade = get_grade(db, user, grade_id)
    for key, value in body.model_dump().items():
        setattr(grade, key, value)
    db.commit()
    return grade


@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.delete(get_grade(db, user, grade_id))
    db.commit()
    return {"ok": True}
