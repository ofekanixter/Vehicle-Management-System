from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.car_repo import CarRepository
from app.repositories.rental_repo import RentalRepository
from app.schemas.rental import RentalCreate, RentalRead
from app.services.rental_service import RentalService

router = APIRouter(prefix="/rentals", tags=["Rentals"])


def get_rental_service(db: Session = Depends(get_db)) -> RentalService:
    return RentalService(CarRepository(db), RentalRepository(db))


@router.post("", response_model=RentalRead, status_code=status.HTTP_201_CREATED)
def create_rental(
    payload: RentalCreate, service: RentalService = Depends(get_rental_service)
):
    return service.register_rental(
        car_id=payload.car_id, customer_name=payload.customer_name
    )


@router.post("/{rental_id}/end", response_model=RentalRead)
def end_rental(rental_id: int, service: RentalService = Depends(get_rental_service)):
    return service.end_rental(rental_id)


@router.get("", response_model=list[RentalRead])
def list_rentals(
    active: Optional[bool] = None,
    service: RentalService = Depends(get_rental_service),
):
    return service.list_rentals(active=active)
