from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..crypto import encrypt
from ..db import get_db
from ..moodle import MoodleClient, MoodleError, run_sync
from ..models import Course, CourseFile, MoodleAccount, User

router = APIRouter(prefix="/api/moodle", tags=["moodle"])


class ConnectIn(BaseModel):
    base_url: str = Field(pattern=r"^https://[^/\s]+")
    token: str = Field(min_length=10, max_length=200)


class StatusOut(BaseModel):
    connected: bool
    base_url: str | None = None
    site_name: str | None = None
    last_sync: datetime | None = None
    last_error: str | None = None
    syncing: bool = False
    courses: int = 0
    files: int = 0


def get_account(db: Session, user: User) -> MoodleAccount | None:
    return db.scalar(select(MoodleAccount).where(MoodleAccount.user_id == user.id))


@router.get("", response_model=StatusOut)
def status(db: Session = Depends(get_db), user: User = Depends(current_user)):
    account = get_account(db, user)
    if account is None:
        return StatusOut(connected=False)
    courses = db.scalar(
        select(func.count(Course.id)).where(Course.user_id == user.id, Course.moodle_course_id.is_not(None))
    )
    files = db.scalar(
        select(func.count(CourseFile.id))
        .join(Course)
        .where(Course.user_id == user.id, CourseFile.moodle_key.is_not(None))
    )
    return StatusOut(
        connected=True,
        base_url=account.base_url,
        site_name=account.site_name,
        last_sync=account.last_sync,
        last_error=account.last_error,
        syncing=account.syncing,
        courses=courses,
        files=files,
    )


@router.put("", response_model=StatusOut)
def connect(
    body: ConnectIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Vérifie la clé auprès de Moodle, l'enregistre chiffrée et lance une première synchro."""
    base_url = body.base_url.rstrip("/")
    try:
        info = MoodleClient(base_url, body.token.strip()).site_info()
    except (MoodleError, ValueError) as exc:
        raise HTTPException(400, f"Moodle a refusé la clé : {exc}")
    except Exception:
        raise HTTPException(400, "Impossible de joindre Moodle à cette adresse")

    account = get_account(db, user) or MoodleAccount(user_id=user.id)
    account.base_url = base_url
    account.token_encrypted = encrypt(body.token.strip())
    account.moodle_user_id = info["userid"]
    account.site_name = info.get("sitename", "")[:255]
    account.last_error = None
    account.syncing = True
    db.add(account)
    db.commit()
    background.add_task(run_sync, account.id)
    return status(db, user)


@router.post("/sync", response_model=StatusOut)
def sync_now(background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(current_user)):
    account = get_account(db, user)
    if account is None:
        raise HTTPException(404, "Moodle n'est pas connecté")
    if not account.syncing:
        account.syncing = True
        db.commit()
        background.add_task(run_sync, account.id)
    return status(db, user)


@router.delete("")
def disconnect(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Supprime la clé. Les cours et fichiers déjà importés sont conservés."""
    account = get_account(db, user)
    if account is not None:
        db.delete(account)
        db.commit()
    return {"ok": True}
