import datetime as dt
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import field_validator


class Entry(SQLModel, table=True):
    id: str = Field(primary_key=True)
    subject: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=4, max_length=1000)
    duration_in_minutes: int = Field(gt=0, le=600)
    date: dt.date
    created_on: dt.datetime

class EntryValidatorsMixin(SQLModel):
    @field_validator("subject", check_fields=False)
    @classmethod
    def normalise_subject(cls, subject):
        if subject is None:
            return subject
        subject = " ".join(subject.split()).casefold()
        if not subject:
            raise ValueError("subject must not be empty")
        return subject
    
    @field_validator("date",check_fields=False)
    @classmethod
    def date_not_in_future(cls, date):
        if date is None:
            return None
        if date > dt.date.today():
            raise ValueError("date must not be in the future")
        return date

class EntryCreate(EntryValidatorsMixin):
    subject: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=4, max_length=1000)
    duration_in_minutes: int = Field(gt=0, le=600)
    date: dt.date


class EntryUpdate(EntryValidatorsMixin):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=4, max_length=1000)
    duration_in_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    date: Optional[dt.date] = Field(default=None)


class FilterEntries(SQLModel):
    subject: str 
    count: int 
    total_minutes: int
