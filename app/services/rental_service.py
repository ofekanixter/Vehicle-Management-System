from typing import Optional

from app.models.models import CarStatus, Rental
from app.repositories.car_repo import CarRepository
from app.repositories.rental_repo import RentalRepository
from app.services.exceptions import (
    CarNotAvailableError,
    CarNotFoundError,
    RentalAlreadyEndedError,
    RentalNotFoundError,
)


class RentalService:
    def __init__(
        self,
        car_repo: CarRepository,
        rental_repo: RentalRepository,
        publisher=None,
    ):
        self.car_repo = car_repo
        self.rental_repo = rental_repo
        self.publisher = publisher

    def register_rental(self, car_id: int, customer_name: str) -> Rental:
        car = self.car_repo.get(car_id)
        if car is None:
            raise CarNotFoundError(car_id)
        if car.status != CarStatus.AVAILABLE:
            raise CarNotAvailableError(car_id)

        rental = self.rental_repo.create(car_id=car_id, customer_name=customer_name)
        self.car_repo.update_status(car, CarStatus.RENTED)
        self.rental_repo.commit()

        self._publish(
            "rental.created",
            {"rental_id": rental.id, "car_id": car.id, "customer": customer_name},
        )
        return rental

    def end_rental(self, rental_id: int) -> Rental:
        rental = self.rental_repo.get(rental_id)
        if rental is None:
            raise RentalNotFoundError(rental_id)
        if rental.end_date is not None:
            raise RentalAlreadyEndedError(rental_id)

        self.rental_repo.end(rental)
        car = self.car_repo.get(rental.car_id)
        self.car_repo.update_status(car, CarStatus.AVAILABLE)
        self.rental_repo.commit()

        self._publish("rental.ended", {"rental_id": rental.id, "car_id": car.id})
        return rental

    def list_rentals(self, active: Optional[bool] = None) -> list[Rental]:
        return self.rental_repo.list(active=active)

    def _publish(self, routing_key: str, body: dict) -> None:
        if self.publisher is not None:
            self.publisher.publish(routing_key, body)
