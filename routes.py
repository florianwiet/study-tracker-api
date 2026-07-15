import uuid
from fastapi import APIRouter, HTTPException, status
from schemas import EntryCreate, EntryOut, EntryUpdate
from storage import load_data, save_data
from datetime import datetime, timezone


router = APIRouter(prefix="/api/v1/entrys", tags=["entry"])

@router.get("/", response_model=list[EntryOut])
def get_entrys():
    """Retrieve all Entrys."""
    entrys = load_data()
    return entrys

@router.post("/", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(entry: EntryCreate):
    """Create a new Entry."""
    entries = load_data()
    new_entry = {
        "id": str(uuid.uuid4()),
        "subject": entry.subject,
        "description": entry.description,
        "duration_in_minutes": entry.duration_in_minutes,
        "date": entry.date,
        "created_on": datetime.now(timezone.utc)
    }
    entries.append(new_entry)
    save_data(entries)
    return new_entry

@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: str):
    """Retrieve a specific Entry by ID."""
    entries = load_data()
    for entry in entries:
        if entry["id"] == entry_id:
            return entry
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

@router.put("/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: str, payload: EntryUpdate):
    """Update an existing Entry."""
    entries = load_data()
    for index, entry in enumerate(entries):
        if entry["id"] == entry_id:
            updated_entry = entry.copy()
            if payload.subject is not None:
                updated_entry["subject"] = payload.subject
            if payload.description is not None:
                updated_entry["description"] = payload.description
            if payload.duration_in_minutes is not None:
                updated_entry["duration_in_minutes"] = payload.duration_in_minutes
            if payload.date is not None:
                updated_entry["date"] = payload.date
            entries[index] = updated_entry
            save_data(entries)
            return updated_entry
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: str):
    """Delete an entry by ID."""
    entries = load_data()
    for index, entry in enumerate(entries):
        if entry["id"] == entry_id:
            entries.pop(index)
            save_data(entries)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

