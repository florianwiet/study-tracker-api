import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from stats import calculate_streak
from tests.routes_test import make_entry

TODAY = dt.date.today()


def days_ago(n: int) -> dt.date:
    return TODAY - dt.timedelta(days=n)


def add_entries(session: Session, *entries):
    for subject, date, minutes in entries:
        session.add(make_entry(subject=subject, description="test", date=date, minutes=minutes))
    session.commit()


# calculate_streak

def test_streak_empty():
    assert calculate_streak(set(), TODAY) == 0


def test_streak_counts_consecutive_days_until_today():
    assert calculate_streak({TODAY, days_ago(1), days_ago(2), days_ago(4)}, TODAY) == 3


def test_streak_starts_yesterday_if_nothing_today():
    assert calculate_streak({days_ago(1), days_ago(2)}, TODAY) == 2


def test_streak_broken_before_yesterday():
    assert calculate_streak({days_ago(2), days_ago(3)}, TODAY) == 0


# /stats/overview

def test_overview_empty_database(client: TestClient):
    response = client.get("/api/v1/stats/overview")

    assert response.status_code == 200
    assert response.json() == {
        "total_entries": 0,
        "total_minutes": 0,
        "minutes_last_7_days": 0,
        "streak_days": 0,
        "subjects": [],
    }


def test_overview_aggregates(client: TestClient, session: Session):
    add_entries(
        session,
        ("math", TODAY, 60),
        ("math", days_ago(1), 30),
        ("physics", days_ago(1), 45),
        ("physics", days_ago(10), 120),
    )

    data = client.get("/api/v1/stats/overview").json()

    assert data["total_entries"] == 4
    assert data["total_minutes"] == 255
    assert data["minutes_last_7_days"] == 135
    assert data["streak_days"] == 2
    # sortiert nach Gesamtminuten absteigend
    assert data["subjects"] == [
        {"subject": "physics", "count": 2, "total_minutes": 165},
        {"subject": "math", "count": 2, "total_minutes": 90},
    ]


# /stats/daily

def test_daily_fills_missing_days_with_zero(client: TestClient, session: Session):
    add_entries(session, ("math", TODAY, 60), ("math", TODAY, 15), ("math", days_ago(2), 30))

    data = client.get("/api/v1/stats/daily?days=3").json()

    assert data == [
        {"date": days_ago(2).isoformat(), "minutes": 30},
        {"date": days_ago(1).isoformat(), "minutes": 0},
        {"date": TODAY.isoformat(), "minutes": 75},
    ]


def test_daily_ignores_entries_outside_window(client: TestClient, session: Session):
    add_entries(session, ("math", days_ago(40), 60))

    data = client.get("/api/v1/stats/daily").json()

    assert len(data) == 30
    assert sum(day["minutes"] for day in data) == 0


def test_daily_filter_by_subject_is_normalised(client: TestClient, session: Session):
    add_entries(session, ("math", TODAY, 60), ("physics", TODAY, 45))

    data = client.get("/api/v1/stats/daily", params={"days": 1, "subject": "  MATH "}).json()

    assert data == [{"date": TODAY.isoformat(), "minutes": 60}]


def test_daily_rejects_invalid_days(client: TestClient):
    assert client.get("/api/v1/stats/daily?days=0").status_code == 422
    assert client.get("/api/v1/stats/daily?days=366").status_code == 422


# /entries pagination, ordering, subjects

def test_entries_newest_first_and_paginated(client: TestClient, session: Session):
    add_entries(session, ("a", days_ago(2), 10), ("b", TODAY, 10), ("c", days_ago(1), 10))

    first_page = client.get("/api/v1/entries/?limit=2").json()
    second_page = client.get("/api/v1/entries/?limit=2&offset=2").json()

    assert [e["subject"] for e in first_page] == ["b", "c"]
    assert [e["subject"] for e in second_page] == ["a"]


def test_entries_invalid_limit(client: TestClient):
    assert client.get("/api/v1/entries/?limit=0").status_code == 422
    assert client.get("/api/v1/entries/?limit=501").status_code == 422


def test_subjects_distinct_and_sorted(client: TestClient, session: Session):
    add_entries(session, ("physics", TODAY, 10), ("math", TODAY, 10), ("math", days_ago(1), 10))

    response = client.get("/api/v1/entries/subjects")

    assert response.status_code == 200
    assert response.json() == ["math", "physics"]


def test_root_redirects_to_dashboard(client: TestClient):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/app/"
