from typing import Optional

from app.models.models import Car, CarStatus
from app.repositories.car_repo import CarRepository
from app.services.exceptions import (
    CarHasActiveRentalError,
    CarHasRentalHistoryError,
    CarNotFoundError,
    InvalidStatusTransitionError,
)

_MANUALLY_SETTABLE_STATUSES = {CarStatus.AVAILABLE, CarStatus.MAINTENANCE}


class CarService:
    def __init__(self, car_repo: CarRepository):
        self.car_repo = car_repo

    def add_car(self, model: str, year: int) -> Car:
        car = self.car_repo.create(model=model, year=year)
        self.car_repo.commit()
        return car

    def list_cars(self, status: Optional[CarStatus] = None) -> list[Car]:
        return self.car_repo.list(status=status)

    def get_car(self, car_id: int) -> Car:
        car = self.car_repo.get(car_id)
        if car is None:
            raise CarNotFoundError(f"Car {car_id} not found")
        return car

    def update_status(self, car_id: int, status: CarStatus) -> Car:
        if status not in _MANUALLY_SETTABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Cannot set car status to '{status.value}' directly"
            )
        car = self.get_car(car_id)
        if car.status == CarStatus.RENTED and status == CarStatus.MAINTENANCE:
            raise CarHasActiveRentalError(
                f"Car {car_id} has an active rental and cannot be moved to maintenance"
            )
        car = self.car_repo.update_status(car, status)
        self.car_repo.commit()
        return car

    def update_details(
        self, car_id: int, model: Optional[str] = None, year: Optional[int] = None
    ) -> Car:
        car = self.get_car(car_id)
        if model is not None:
            car.model = model
        if year is not None:
            car.year = year
        self.car_repo.commit()
        return car

    def delete_car(self, car_id: int) -> None:
        car = self.get_car(car_id)
        if self.car_repo.has_rentals(car.id):
            raise CarHasRentalHistoryError(
                f"Car {car_id} has rental history and cannot be deleted"
            )
        self.car_repo.delete(car)
        self.car_repo.commit()
