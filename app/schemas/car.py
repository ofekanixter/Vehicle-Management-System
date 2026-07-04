from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import CarStatus

# Next model-year cars are sold before the calendar year starts.
_MAX_YEAR = date.today().year + 1


class CarCreate(BaseModel):
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1950, le=_MAX_YEAR)


class CarUpdate(BaseModel):
    model: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1950, le=_MAX_YEAR)
    status: Optional[CarStatus] = None


class CarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model: str
    year: int
    status: CarStatus
    created_at: datetime
    updated_at: datetime
