from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Course, Event, Grade, User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Jours avant un examen où l'on conseille une session de révision.
REVISION_DAYS = [7, 3, 1]


@router.get("")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    today = date.today()
    day_start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    today_events = db.scalars(
        select(Event)
        .where(Event.user_id == user.id, Event.start >= day_start, Event.start < day_start + timedelta(days=1))
        .order_by(Event.start)
    ).all()

    exams = db.scalars(
        select(Event)
        .where(Event.user_id == user.id, Event.kind == "exam", Event.start >= now)
        .where(Event.start <= now + timedelta(days=45))
        .order_by(Event.start)
    ).all()

    reviews = db.scalars(
        select(Course)
        .where(Course.user_id == user.id, Course.next_review <= today)
        .order_by(Course.next_review)
    ).all()

    recent_courses = db.scalars(
        select(Course).where(Course.user_id == user.id).order_by(Course.created_at.desc()).limit(5)
    ).all()

    grades = db.scalars(select(Grade).where(Grade.user_id == user.id)).all()
    total_coef = sum(g.coefficient for g in grades)
    average = (
        sum(g.value / g.max_value * 20 * g.coefficient for g in grades) / total_coef if total_coef else None
    )

    def event_dict(e: Event):
        return {"id": e.id, "title": e.title, "start": e.start, "end": e.end, "location": e.location, "kind": e.kind}

    exam_items = []
    for e in exams:
        days_left = (e.start.date() - today).days
        exam_items.append(
            {
                **event_dict(e),
                "days_left": days_left,
                "revise_today": days_left in REVISION_DAYS or days_left == 0,
                "revision_dates": [e.start.date() - timedelta(days=d) for d in REVISION_DAYS if d <= days_left],
            }
        )

    return {
        "user": {"name": user.name},
        "today": [event_dict(e) for e in today_events],
        "exams": exam_items,
        "reviews": [
            {"id": c.id, "title": c.title, "subject": c.subject, "next_review": c.next_review} for c in reviews
        ],
        "recent_courses": [
            {"id": c.id, "title": c.title, "subject": c.subject, "created_at": c.created_at} for c in recent_courses
        ],
        "average": round(average, 2) if average is not None else None,
        "grade_count": len(grades),
    }
