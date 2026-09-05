from fastapi.testclient import TestClient
from sqlmodel import Session
import uuid
import datetime as dt
from schemas import Entry


def make_payload(subject: str, description: str, date: dt.date, minutes: int):
    """Entry for the API"""
    return {
        "subject": subject,
        "description": description,
        "date": date.isoformat(),
        "duration_in_minutes": minutes,
    }

def make_entry(subject: str, description: str, date: dt.date, minutes: int):
    """Entry-Object to directly write into the database"""
    entry = Entry(
        id = str(uuid.uuid4()),
        created_on=dt.datetime.now(dt.timezone.utc),
        subject=subject,
        description=description,
        duration_in_minutes=minutes,
        date=date
    )
    return entry


def create_entry_via_api(client: TestClient, subject="math", description="test description",
                         date=None, minutes=60):
    """Create an entry through the API and return the response body"""
    payload = make_payload(subject=subject,
                           description=description,
                           date=date or dt.date.today(),
                           minutes=minutes)
    response = client.post("/api/v1/entries/", json=payload)
    assert response.status_code == 201
    return response.json()


# Test CRUD-Routes:

def test_create_entry(client: TestClient):
    payload = make_payload(subject="math",
                           description="Test description",
                           date=dt.date.today(),
                           minutes=20)

    response = client.post("/api/v1/entries/", json=payload)
    data = response.json()

    assert response.status_code == 201
    assert data["date"] == dt.date.today().isoformat()
    assert data["description"] == "Test description"
    assert data["duration_in_minutes"] == 20
    assert data["subject"] == "math"
    assert data["id"]
    assert data["created_on"]

def test_create_entry_normalises_subject(client: TestClient):
    payload = make_payload(subject="  MaTh   Basics  ",
                           description="test description",
                           date=dt.date.today(),
                           minutes=20)

    response = client.post("/api/v1/entries/", json=payload)

    assert response.status_code == 201
    assert response.json()["subject"] == "math basics"

def test_create_entry_without_description(client: TestClient):
    response = client.post("/api/v1/entries/", json={
        "subject": "math",
        "date": dt.date.today().isoformat(),
        "duration_in_minutes": 20,
    })

    assert response.status_code == 201
    assert response.json()["description"] is None

def test_read_entries(session: Session, client: TestClient):
    entry = make_entry(subject="test subject",
                       description="test description",
                       date=dt.date.today(),
                       minutes=60)

    session.add(entry)
    session.commit()

    response = client.get("/api/v1/entries/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["subject"] == "test subject"

def test_read_entries_empty(client: TestClient):
    response = client.get("/api/v1/entries/")

    assert response.status_code == 200
    assert response.json() == []


# Test single entry route:

def test_get_single_entry(session: Session, client: TestClient):
    entry = make_entry(subject="math",
                       description="test description",
                       date=dt.date.today(),
                       minutes=45)
    session.add(entry)
    session.commit()

    response = client.get(f"/api/v1/entries/{entry.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == entry.id
    assert data["subject"] == "math"
    assert data["duration_in_minutes"] == 45

def test_get_single_entry_not_found(client: TestClient):
    response = client.get("/api/v1/entries/unknown-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


# Test update route:

def test_update_entry_changes_only_given_fields(session: Session, client: TestClient):
    entry = make_entry(subject="math",
                       description="test description",
                       date=dt.date.today(),
                       minutes=60)
    session.add(entry)
    session.commit()

    response = client.patch(f"/api/v1/entries/{entry.id}",
                            json={"duration_in_minutes": 30})
    data = response.json()

    assert response.status_code == 200
    assert data["duration_in_minutes"] == 30
    assert data["subject"] == "math"
    assert data["description"] == "test description"
    assert data["date"] == dt.date.today().isoformat()

def test_update_entry_normalises_subject(session: Session, client: TestClient):
    entry = make_entry(subject="math",
                       description="test description",
                       date=dt.date.today(),
                       minutes=60)
    session.add(entry)
    session.commit()

    response = client.patch(f"/api/v1/entries/{entry.id}",
                            json={"subject": "  PhYsIcs   II "})

    assert response.status_code == 200
    assert response.json()["subject"] == "physics ii"

def test_update_entry_not_found(client: TestClient):
    response = client.patch("/api/v1/entries/unknown-id",
                            json={"duration_in_minutes": 30})

    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"

def test_update_entry_invalid_value_rejected(session: Session, client: TestClient):
    entry = make_entry(subject="math",
                       description="test description",
                       date=dt.date.today(),
                       minutes=60)
    session.add(entry)
    session.commit()

    response = client.patch(f"/api/v1/entries/{entry.id}",
                            json={"duration_in_minutes": 0})

    assert response.status_code == 422


# Test delete route:

def test_delete_entry(client: TestClient):
    created = create_entry_via_api(client)

    response = client.delete(f"/api/v1/entries/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    assert client.get(f"/api/v1/entries/{created['id']}").status_code == 404

def test_delete_router(client: TestClient):
    response = client.delete("/api/v1/entries/unknown-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


# Test filter route:

def test_filter_by_subject(session: Session, client: TestClient):
    session.add(make_entry(subject="math",
                           description="test description",
                           date=dt.date.today(),
                           minutes=30))
    session.add(make_entry(subject="physics",
                           description="test description",
                           date=dt.date.today(),
                           minutes=90))
    session.commit()

    response = client.get("/api/v1/entries/filter", params={"subject": "  MaTh "})
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["subject"] == "math"

def test_filter_by_date_range(session: Session, client: TestClient):
    today = dt.date.today()
    for offset in (5, 2, 0):
        session.add(make_entry(subject="math",
                               description="test description",
                               date=today - dt.timedelta(days=offset),
                               minutes=30))
    session.commit()

    start = (today - dt.timedelta(days=2)).isoformat()
    end = today.isoformat()

    only_start = client.get("/api/v1/entries/filter", params={"start_date": start})
    only_end = client.get("/api/v1/entries/filter", params={"end_date": start})
    both = client.get("/api/v1/entries/filter",
                      params={"start_date": start, "end_date": start})
    full_range = client.get("/api/v1/entries/filter",
                            params={"start_date": start, "end_date": end})

    # boundaries are inclusive on both sides
    assert len(only_start.json()) == 2
    assert len(only_end.json()) == 2
    assert len(both.json()) == 1
    assert len(full_range.json()) == 2

def test_filter_by_subject_and_date_range(session: Session, client: TestClient):
    today = dt.date.today()
    session.add(make_entry(subject="math",
                           description="test description",
                           date=today,
                           minutes=30))
    session.add(make_entry(subject="math",
                           description="test description",
                           date=today - dt.timedelta(days=10),
                           minutes=30))
    session.add(make_entry(subject="physics",
                           description="test description",
                           date=today,
                           minutes=30))
    session.commit()

    response = client.get("/api/v1/entries/filter", params={
        "subject": "math",
        "start_date": (today - dt.timedelta(days=1)).isoformat(),
    })
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["subject"] == "math"
    assert data[0]["date"] == today.isoformat()

def test_filter_without_params_returns_all(session: Session, client: TestClient):
    """'/filter' must not be swallowed by the '/{entry_id}' route"""
    session.add(make_entry(subject="math",
                           description="test description",
                           date=dt.date.today(),
                           minutes=30))
    session.commit()

    response = client.get("/api/v1/entries/filter")

    assert response.status_code == 200
    assert len(response.json()) == 1

def test_filter_no_matches_returns_empty_list(client: TestClient):
    response = client.get("/api/v1/entries/filter", params={"subject": "unknown"})

    assert response.status_code == 200
    assert response.json() == []

def test_filter_invalid_date_range_returns_400(client: TestClient):
    today = dt.date.today()
    response = client.get("/api/v1/entries/filter", params={
        "start_date": today.isoformat(),
        "end_date": (today - dt.timedelta(days=1)).isoformat(),
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "start_date greater then end_date"

def test_filter_invalid_date_format_returns_422(client: TestClient):
    response = client.get("/api/v1/entries/filter", params={"start_date": "not-a-date"})

    assert response.status_code == 422


# Test statistic route:

def test_subject_statistic(session: Session, client: TestClient):
    for minutes in (30, 45):
        session.add(make_entry(subject="math",
                               description="test description",
                               date=dt.date.today(),
                               minutes=minutes))
        
    session.add(make_entry(subject="physics",
                           description="other subject",
                           date=dt.date.today(),
                           minutes=90))
    
    session.commit()

    response = client.get("/api/v1/entries/statistic/Math")
    data = response.json()

    assert response.status_code == 200
    assert data["subject"] == "math"
    assert data["count"] == 2
    assert data["total_minutes"] == 75

def test_subject_statistic_error(client: TestClient):
    response = client.get("/api/v1/entries/statistic/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "subject not found"


# Test validation (via API):

def test_create_entry_future_date_rejected(client: TestClient):
    payload = make_payload(subject="math",
                           description="test description",
                           date=dt.date.today() + dt.timedelta(days=1),
                           minutes=20)

    response = client.post("/api/v1/entries/", json=payload)

    assert response.status_code == 422

def test_create_entry_duration_zero_rejected(client: TestClient):
    payload = make_payload(subject="math",
                           description="test description",
                           date=dt.date.today(),
                           minutes=0)

    assert client.post("/api/v1/entries/", json=payload).status_code == 422

def test_create_entry_duration_too_high_rejected(client: TestClient):
    payload = make_payload(subject="math",
                           description="test description",
                           date=dt.date.today(),
                           minutes=601)

    assert client.post("/api/v1/entries/", json=payload).status_code == 422

def test_create_entry_description_too_short_rejected(client: TestClient):
    payload = make_payload(subject="math",
                           description="abc",
                           date=dt.date.today(),
                           minutes=20)

    assert client.post("/api/v1/entries/", json=payload).status_code == 422

def test_create_entry_subject_too_long_rejected(client: TestClient):
    payload = make_payload(subject="x" * 51,
                           description="test description",
                           date=dt.date.today(),
                           minutes=20)

    assert client.post("/api/v1/entries/", json=payload).status_code == 422

def test_create_entry_whitespace_only_subject_rejected(client: TestClient):
    payload = make_payload(subject="   ",
                           description="test description",
                           date=dt.date.today(),
                           minutes=20)

    assert client.post("/api/v1/entries/", json=payload).status_code == 422

def test_create_entry_missing_required_field_rejected(client: TestClient):
    response = client.post("/api/v1/entries/", json={"subject": "math"})

    assert response.status_code == 422


# Test app level (main.py):

def test_health_check(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_process_time_header_present(client: TestClient):
    response = client.get("/api/v1/entries/")

    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("s")
