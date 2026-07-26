from fastapi.testclient import TestClient
import datetime as dt


def test_create_entry(client: TestClient):
    response = client.post(
        "/api/v1/entries/", json={"subject": "Math", 
                                  "description": "Test description",
                                  "duration_in_minutes": 20,
                                  "date": dt.date.today().isoformat()}
    )

    data = response.json()

    assert response.status_code == 201
    assert data["date"] == dt.date.today().isoformat()
    assert data["description"] == "Test description"
    assert data["duration_in_minutes"] == 20
    assert data["subject"] == "math"