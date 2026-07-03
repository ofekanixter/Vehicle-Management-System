from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RentalCreate(BaseModel):
    car_id: int
    customer_name: str = Field(min_length=1, max_length=100)


class RentalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: int
    customer_name: str
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
