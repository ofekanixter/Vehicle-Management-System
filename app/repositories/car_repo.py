import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Car, CarStatus, Rental

logger = logging.getLogger(__name__)


class CarRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, model: str, year: int) -> Car:
        car = Car(model=model, year=year)
        self.session.add(car)
        self.session.flush()
        logger.debug("car %s flushed (model=%s, year=%s, pending commit)", car.id, model, year)
        return car

    def get(self, car_id: int) -> Optional[Car]:
        car = self.session.get(Car, car_id)
        logger.debug("car %s lookup: %s", car_id, "found" if car else "not found")
        return car

    def list(self, status: Optional[CarStatus] = None) -> list[Car]:
        query = self.session.query(Car)
        if status is not None:
            query = query.filter(Car.status == status)
        cars = query.all()
        logger.debug("car query returned %d car(s) (status=%s)", len(cars), status.value if status else "any")
        return cars

    def update_status(self, car: Car, status: CarStatus) -> Car:
        car.status = status
        self.session.flush()
        logger.debug("car %s status flushed to %s (pending commit)", car.id, status.value)
        return car

    def count_by_status(self) -> dict:
        rows = self.session.query(Car.status, func.count(Car.id)).group_by(Car.status).all()
        counts = {status.value: 0 for status in CarStatus}
        for status, count in rows:
            counts[status.value] = count
        logger.debug("car status counts: %s", counts)
        return counts

    def has_rentals(self, car_id: int) -> bool:
        result = (
            self.session.query(Rental.id).filter(Rental.car_id == car_id).first()
            is not None
        )
        logger.debug("car %s has_rentals check: %s", car_id, result)
        return result

    def delete(self, car: Car) -> None:
        car_id = car.id
        self.session.delete(car)
        self.session.flush()
        logger.debug("car %s flushed for delete (pending commit)", car_id)

    def commit(self) -> None:
        self.session.commit()
        logger.debug("transaction committed")

    def rollback(self) -> None:
        self.session.rollback()
        logger.debug("transaction rolled back")
