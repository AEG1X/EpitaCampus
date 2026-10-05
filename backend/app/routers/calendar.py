from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..icsync import sync_source
from ..models import CalendarSource, Event, User

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class SourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(pattern=r"^(https?|webcal)://")


class SourceOut(BaseModel):
    id: int
    name: str
    url: str
    last_sync: datetime | None
    last_error: str | None


class EventIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    start: datetime
    end: datetime
    location: str = ""
    description: str = ""
    kind: str = Field(default="other", pattern="^(course|exam|other)$")


class EventOut(EventIn):
    id: int
    source_id: int | None


class KindIn(BaseModel):
    kind: str = Field(pattern="^(course|exam|other)$")


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(CalendarSource).where(CalendarSource.user_id == user.id)).all()


@router.post("/sources", response_model=SourceOut)
def add_source(body: SourceIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    url = body.url.replace("webcal://", "https://", 1)
    source = CalendarSource(user_id=user.id, name=body.name, url=url)
    db.add(source)
    db.commit()
    try:
        sync_source(db, source)
    except Exception:
        pass  # l'erreur est enregistrée dans last_error et affichée dans l'interface
    return source


def get_source(db: Session, user: User, source_id: int) -> CalendarSource:
    source = db.get(CalendarSource, source_id)
    if source is None or source.user_id != user.id:
        raise HTTPException(404, "Calendrier introuvable")
    return source


@router.post("/sources/{source_id}/sync", response_model=SourceOut)
def resync(source_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    source = get_source(db, user, source_id)
    try:
        sync_source(db, source)
    except Exception:
        pass
    return source


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    source = get_source(db, user, source_id)
    for event in db.scalars(select(Event).where(Event.source_id == source.id)):
        db.delete(event)
    db.delete(source)
    db.commit()
    return {"ok": True}


@router.get("/events", response_model=list[EventOut])
def list_events(
    start: datetime, end: datetime, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    query = (
        select(Event)
        .where(Event.user_id == user.id, Event.end >= start, Event.start <= end)
        .order_by(Event.start)
    )
    return db.scalars(query).all()


@router.post("/events", response_model=EventOut)
def add_event(body: EventIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    event = Event(user_id=user.id, **body.model_dump())
    db.add(event)
    db.commit()
    return event


def get_event(db: Session, user: User, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None or event.user_id != user.id:
        raise HTTPException(404, "Événement introuvable")
    return event


@router.patch("/events/{event_id}/kind", response_model=EventOut)
def set_kind(
    event_id: int, body: KindIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    event = get_event(db, user, event_id)
    event.kind = body.kind
    db.commit()
    return event


@router.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    event = get_event(db, user, event_id)
    if event.source_id is not None:
        raise HTTPException(400, "Cet événement vient d'un calendrier synchronisé")
    db.delete(event)
    db.commit()
    return {"ok": True}
