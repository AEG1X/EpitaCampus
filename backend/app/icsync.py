"""Synchronisation des calendriers ICS (Zeus, Google Agenda, etc.)."""

import asyncio
import ipaddress
import socket
import logging
import re
from urllib.parse import urlparse
from datetime import date, datetime, time, timezone

import httpx
from icalendar import Calendar
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal
from .models import CalendarSource, Event

log = logging.getLogger("campus.icsync")

EXAM_PATTERN = re.compile(r"\b(exam|examen|partiel|midterm|final|qcm|contr[oô]le|DS|soutenance)\b", re.I)


def guess_kind(title: str) -> str:
    return "exam" if EXAM_PATTERN.search(title) else "course"


def to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    raise ValueError(f"Date invalide : {value!r}")


def parse_ics(content: bytes) -> list[dict]:
    events = []
    for comp in Calendar.from_ical(content).walk("VEVENT"):
        if comp.get("DTSTART") is None:
            continue
        start = to_datetime(comp.decoded("DTSTART"))
        end = to_datetime(comp.decoded("DTEND")) if comp.get("DTEND") else start
        title = str(comp.get("SUMMARY", "Sans titre"))
        events.append(
            {
                "uid": str(comp.get("UID") or f"{title}-{start.isoformat()}")[:500],
                "title": title[:300],
                "start": start,
                "end": end,
                "location": str(comp.get("LOCATION", ""))[:300],
                "description": str(comp.get("DESCRIPTION", "")),
                "kind": guess_kind(title),
            }
        )
    return events


def check_url(url: str) -> None:
    """Refuse les liens vers le réseau local ou la machine elle-même."""
    host = urlparse(url).hostname
    if not host:
        raise ValueError("Lien invalide")
    if settings.allow_private_ics:
        return
    for info in socket.getaddrinfo(host, None):
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError("Les liens vers le réseau local ne sont pas autorisés")


def sync_source(db: Session, source: CalendarSource) -> int:
    """Remplace les événements de la source par ceux du flux ICS. Renvoie le nombre d'événements."""
    try:
        check_url(source.url)
        resp = httpx.get(source.url, timeout=30, follow_redirects=False)
        if resp.is_redirect:
            # On suit au plus une redirection, en revérifiant la destination.
            target = str(resp.next_request.url)
            check_url(target)
            resp = httpx.get(target, timeout=30)
        resp.raise_for_status()
        parsed = parse_ics(resp.content)
    except Exception as exc:  # noqa: BLE001 - on veut garder l'erreur pour l'afficher
        source.last_error = str(exc)[:500]
        db.commit()
        raise

    existing = {e.uid: e for e in db.scalars(select(Event).where(Event.source_id == source.id))}
    seen = set()
    for data in parsed:
        if data["uid"] in seen:
            continue
        seen.add(data["uid"])
        event = existing.get(data["uid"])
        if event is None:
            db.add(Event(user_id=source.user_id, source_id=source.id, **data))
        else:
            # On garde le type choisi à la main si l'utilisateur l'a modifié.
            data.pop("kind")
            for key, value in data.items():
                setattr(event, key, value)
    for uid, event in existing.items():
        if uid not in seen:
            db.delete(event)
    source.last_sync = datetime.now(timezone.utc)
    source.last_error = None
    db.commit()
    return len(seen)


def sync_all() -> None:
    with SessionLocal() as db:
        for source in db.scalars(select(CalendarSource)).all():
            try:
                count = sync_source(db, source)
                log.info("Calendrier %s synchronisé (%d événements)", source.name, count)
            except Exception:
                log.exception("Échec de synchronisation du calendrier %s", source.name)


async def sync_loop() -> None:
    while True:
        await asyncio.to_thread(sync_all)
        await asyncio.sleep(settings.calendar_sync_minutes * 60)
