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

def test_delete_router(client: TestClient):
    response = client.delete("/api/v1/entries/unknown-id")
    assert response.status_code == 404

