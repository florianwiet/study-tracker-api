import datetime as dt
from typing import Optional
from sqlmodel import SQLModel, Field

class Entry(SQLModel, table=True):
    id: str = Field(primary_key=True)
    subject: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    duration_in_minutes: int = Field(gt=0, le=600)
    date: dt.date = Field(le=dt.date.today())
    created_on: dt.datetime


class EntryCreate(SQLModel):
    subject: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    duration_in_minutes: int = Field(gt=0, le=600)
    date: dt.date = Field(le=dt.date.today())

class EntryUpdate(SQLModel):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    duration_in_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    date: Optional[dt.date] = Field(default=None, le=dt.date.today())
