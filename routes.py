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
    
