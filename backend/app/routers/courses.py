import uuid
from pathlib import Path
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import current_user
from ..config import settings
from ..db import get_db
from ..models import Course, CourseFile, User

router = APIRouter(prefix="/api/courses", tags=["courses"])

# Intervalles de révision espacée (en jours) après chaque révision.
REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60]
MAX_UPLOAD = 100 * 1024 * 1024
INLINE_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "txt": "text/plain; charset=utf-8",
}


class CourseIn(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""


class FileOut(BaseModel):
    id: int
    filename: str
    size: int
    section: str | None = None
    uploaded_at: datetime


class CourseOut(BaseModel):
    id: int
    subject: str
    title: str
    notes: str
    next_review: date | None
    review_count: int
    moodle_course_id: int | None = None
    created_at: datetime
    files: list[FileOut]


def files_dir():
    path = settings.data_dir / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_course(db: Session, user: User, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None or course.user_id != user.id:
        raise HTTPException(404, "Cours introuvable")
    return course


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = (
        select(Course)
        .where(Course.user_id == user.id)
        .options(selectinload(Course.files))
        .order_by(Course.created_at.desc())
    )
    return db.scalars(query).all()


@router.post("", response_model=CourseOut)
def create_course(body: CourseIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    course = Course(user_id=user.id, next_review=date.today() + timedelta(days=1), **body.model_dump())
    db.add(course)
    db.commit()
    return course


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int, body: CourseIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    course = get_course(db, user, course_id)
    for key, value in body.model_dump().items():
        setattr(course, key, value)
    db.commit()
    return course


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    course = get_course(db, user, course_id)
    for f in course.files:
        (files_dir() / f.stored_name).unlink(missing_ok=True)
    db.delete(course)
    db.commit()
    return {"ok": True}


@router.post("/{course_id}/review", response_model=CourseOut)
def mark_reviewed(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Marque le cours comme révisé et planifie la prochaine révision."""
    course = get_course(db, user, course_id)
    interval = REVIEW_INTERVALS[min(course.review_count, len(REVIEW_INTERVALS) - 1)]
    course.review_count += 1
    course.next_review = date.today() + timedelta(days=interval)
    db.commit()
    return course


@router.post("/{course_id}/files", response_model=FileOut)
async def upload_file(
    course_id: int, file: UploadFile, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    course = get_course(db, user, course_id)
    filename = Path(file.filename or "fichier").name[:255]
    suffix = "".join(c for c in filename.rsplit(".", 1)[-1][:10] if c.isalnum()).lower()
    stored = f"{uuid.uuid4().hex}.{suffix or 'bin'}"
    path = files_dir() / stored
    size = 0
    # Écriture par morceaux pour ne pas charger 100 Mo en mémoire sur le Pi.
    with path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD:
                out.close()
                path.unlink(missing_ok=True)
                raise HTTPException(413, "Fichier trop gros (100 Mo max)")
            out.write(chunk)
    record = CourseFile(course_id=course.id, filename=filename, stored_name=stored, size=size)
    db.add(record)
    db.commit()
    return record


def get_file(db: Session, user: User, file_id: int) -> CourseFile:
    record = db.get(CourseFile, file_id)
    if record is None or record.course.user_id != user.id:
        raise HTTPException(404, "Fichier introuvable")
    return record


@router.get("/files/{file_id}")
def download_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = get_file(db, user, file_id)
    suffix = record.stored_name.rsplit(".", 1)[-1]
    # Seuls les PDF et images s'ouvrent dans le navigateur ; le reste est téléchargé, pour
    # qu'un fichier HTML déposé ne puisse jamais s'exécuter sur le site.
    media_type = INLINE_TYPES.get(suffix)
    return FileResponse(
        files_dir() / record.stored_name,
        filename=record.filename,
        media_type=media_type or "application/octet-stream",
        content_disposition_type="inline" if media_type else "attachment",
        headers={"Content-Security-Policy": "sandbox", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = get_file(db, user, file_id)
    (files_dir() / record.stored_name).unlink(missing_ok=True)
    db.delete(record)
    db.commit()
    return {"ok": True}
