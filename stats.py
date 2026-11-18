import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select

from db import get_session
from schemas import DailyMinutes, Entry, Overview, SubjectStatistic

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


def calculate_streak(days_with_entries: set[dt.date], today: dt.date) -> int:
    """Count consecutive days with at least one entry, ending today.

    If there is nothing for today yet, the streak still counts up to
    yesterday, so it does not drop to 0 in the morning.
    """
    day = today if today in days_with_entries else today - dt.timedelta(days=1)
    streak = 0
    while day in days_with_entries:
        streak += 1
        day -= dt.timedelta(days=1)
    return streak


@router.get("/overview", response_model=Overview)
def get_overview(session: Session = Depends(get_session)):
    """Totals, last 7 days, current streak and minutes per subject"""
    today = dt.date.today()

    total_entries, total_minutes = session.exec(
        select(func.count(Entry.id), func.coalesce(func.sum(Entry.duration_in_minutes), 0))
    ).one()

    minutes_last_7_days = session.exec(
        select(func.coalesce(func.sum(Entry.duration_in_minutes), 0)).where(
            Entry.date > today - dt.timedelta(days=7)
        )
    ).one()

    subject_rows = session.exec(
        select(Entry.subject, func.count(Entry.id), func.sum(Entry.duration_in_minutes))
        .group_by(Entry.subject)
        .order_by(func.sum(Entry.duration_in_minutes).desc())
    ).all()

    days_with_entries = set(session.exec(select(Entry.date).distinct()).all())

    return Overview(
        total_entries=total_entries,
        total_minutes=total_minutes,
        minutes_last_7_days=minutes_last_7_days,
        streak_days=calculate_streak(days_with_entries, today),
        subjects=[
            SubjectStatistic(subject=subject, count=count, total_minutes=minutes)
            for subject, count, minutes in subject_rows
        ],
    )


@router.get("/daily", response_model=list[DailyMinutes])
def get_daily(
    days: int = Query(default=30, ge=1, le=365),
    subject: str | None = None,
    session: Session = Depends(get_session),
):
    """Minutes per day for the last `days` days, days without entries are 0"""
    today = dt.date.today()
    start = today - dt.timedelta(days=days - 1)

    statement = (
        select(Entry.date, func.sum(Entry.duration_in_minutes))
        .where(Entry.date >= start)
        .group_by(Entry.date)
    )
    if subject:
        statement = statement.where(Entry.subject == " ".join(subject.split()).casefold())

    minutes_by_day = dict(session.exec(statement).all())

    return [
        DailyMinutes(date=day, minutes=minutes_by_day.get(day, 0))
        for day in (start + dt.timedelta(days=i) for i in range(days))
    ]
