import datetime as dt
from pydantic import BaseModel, Field
from typing import Optional

class EntryCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    duration_in_minutes: int = Field(gt=0, le=600)
    date: dt.date = Field(le=dt.date.today())

class EntryUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    duration_in_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    date: Optional[dt.date] = Field(default=None, le=dt.date.today())

class EntryOut(BaseModel):
    id: str
    subject: str
    description: Optional[str]
    duration_in_minutes: int
    date: dt.date
    created_on: dt.datetime
