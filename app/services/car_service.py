import logging
from typing import Optional

from app.core.metrics import set_cars_gauge
from app.models.models import Car, CarStatus
from app.repositories.car_repo import CarRepository
from app.services.exceptions import (
    CarHasActiveRentalError,
    CarHasRentalHistoryError,
    CarNotFoundError,
    InvalidStatusTransitionError,
)

logger = logging.getLogger(__name__)

_MANUALLY_SETTABLE_STATUSES = {CarStatus.AVAILABLE, CarStatus.MAINTENANCE}


class CarService:
    def __init__(self, car_repo: CarRepository):
        self.car_repo = car_repo

    def add_car(self, model: str, year: int) -> Car:
        car = self.car_repo.create(model=model, year=year)
        self.car_repo.commit()
        set_cars_gauge(self.car_repo.count_by_status())
        logger.info("car %s added (model=%s, year=%s)", car.id, car.model, car.year)
        return car

    def list_cars(self, status: Optional[CarStatus] = None) -> list[Car]:
        cars = self.car_repo.list(status=status)
        logger.debug("list_cars returned %d car(s) (status=%s)", len(cars), status.value if status else "any")
        return cars

    def get_car(self, car_id: int) -> Car:
        car = self.car_repo.get(car_id)
        if car is None:
            raise CarNotFoundError(f"Car {car_id} not found")
        logger.debug("car %s retrieved", car_id)
        return car

    def update_status(self, car_id: int, status: CarStatus) -> Car:
        if status not in _MANUALLY_SETTABLE_STATUSES:
            logger.warning(
                "rejected direct status change on car %s to '%s'", car_id, status.value
            )
            raise InvalidStatusTransitionError(
                f"Cannot set car status to '{status.value}' directly"
            )
        car = self.get_car(car_id)
        if car.status == CarStatus.RENTED and status == CarStatus.MAINTENANCE:
            logger.warning(
                "rejected maintenance transition for car %s: active rental", car_id
            )
            raise CarHasActiveRentalError(
                f"Car {car_id} has an active rental and cannot be moved to maintenance"
            )
        car = self.car_repo.update_status(car, status)
        self.car_repo.commit()
        set_cars_gauge(self.car_repo.count_by_status())
        logger.info("car %s status updated to %s", car.id, status.value)
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
        logger.info("car %s updated (model=%s, year=%s)", car.id, car.model, car.year)
        return car

    def delete_car(self, car_id: int) -> None:
        car = self.get_car(car_id)
        if self.car_repo.has_rentals(car.id):
            logger.warning(
                "rejected delete of car %s: has rental history", car_id
            )
            raise CarHasRentalHistoryError(
                f"Car {car_id} has rental history and cannot be deleted"
            )
        self.car_repo.delete(car)
        self.car_repo.commit()
        set_cars_gauge(self.car_repo.count_by_status())
        logger.info("car %s deleted", car_id)
