from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import CarStatus
from app.repositories.car_repo import CarRepository
from app.schemas.car import CarCreate, CarRead, CarUpdate
from app.services.car_service import CarService

router = APIRouter(prefix="/cars", tags=["Cars"])


def get_car_service(db: Session = Depends(get_db)) -> CarService:
    return CarService(CarRepository(db))


@router.post("", response_model=CarRead, status_code=status.HTTP_201_CREATED)
def create_car(payload: CarCreate, service: CarService = Depends(get_car_service)):
    return service.add_car(model=payload.model, year=payload.year)


@router.get("", response_model=list[CarRead])
def list_cars(
    status: Optional[CarStatus] = None,
    service: CarService = Depends(get_car_service),
):
    return service.list_cars(status=status)


@router.get("/{car_id}", response_model=CarRead)
def get_car(car_id: int, service: CarService = Depends(get_car_service)):
    return service.get_car(car_id)


@router.patch("/{car_id}", response_model=CarRead)
def update_car(
    car_id: int, payload: CarUpdate, service: CarService = Depends(get_car_service)
):
    car = None
    if payload.status is not None:
        car = service.update_status(car_id, payload.status)
    if payload.model is not None or payload.year is not None:
        car = service.update_details(car_id, model=payload.model, year=payload.year)
    return car if car is not None else service.get_car(car_id)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(car_id: int, service: CarService = Depends(get_car_service)):
    service.delete_car(car_id)
