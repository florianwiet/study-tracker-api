import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from sqlmodel import Session, select

from db import get_session
from schemas import Entry, EntryCreate, EntryUpdate


router = APIRouter(prefix="/api/v1/entries", tags=["entry"])


# BUILDING CRUD ROUTES

"""Create a new Entry"""
@router.post("/", response_model=Entry, status_code=status.HTTP_201_CREATED)
def create_entry(payload:EntryCreate, session: Session = Depends(get_session)):
    new_entry = Entry(id=str(uuid.uuid4()),
                      created_on=datetime.now(timezone.utc),
                      **payload.model_dump())
    session.add(new_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry

"""get all entries"""
@router.get("/", response_model=List[Entry])
def get_entries(session: Session = Depends(get_session)):
    entries = session.exec(select(Entry)).all()
    return entries
    
"""get a single entrie"""
@router.get("/{entry_id}", response_model=Entry)
def get_entry(entry_id: str, session: Session = Depends(get_session)):
    entry = session.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


"""update Entry"""
@router.patch("/{entry_id}", response_model=Entry)
def update_entry(entry_id: str, payload: EntryUpdate, session: Session = Depends(get_session)):
    entry = session.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(entry, key, value)

    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

"""delete Entry"""
@router.delete("/{entry_id}")
def delete_entry(entry_id: str, session: Session = Depends(get_session)):
    entry = session.get(Entry, entry_id)
    if not entry: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    session.delete(entry)
    session.commit()
    return {"deleted":True}