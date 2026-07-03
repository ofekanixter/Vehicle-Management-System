import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.core.metrics import ONGOING_RENTALS, RENTALS_CREATED, set_cars_gauge
from app.models.models import CarStatus, Rental
from app.repositories.car_repo import CarRepository
from app.repositories.rental_repo import RentalRepository
from app.services.exceptions import (
    CarNotAvailableError,
    CarNotFoundError,
    RentalAlreadyEndedError,
    RentalNotFoundError,
)

logger = logging.getLogger(__name__)


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
            raise CarNotFoundError(f"Car {car_id} not found")
        if car.status != CarStatus.AVAILABLE:
            logger.warning(
                "rejected rental for car %s: status is %s", car_id, car.status.value
            )
            raise CarNotAvailableError(
                f"Car {car_id} is not available (status: {car.status.value})"
            )

        try:
            rental = self.rental_repo.create(car_id=car_id, customer_name=customer_name)
            self.car_repo.update_status(car, CarStatus.RENTED)
            self.rental_repo.commit()
        except IntegrityError:
            # The one_active_rental_per_car index caught a rental this
            # transaction couldn't see (concurrent request) — the DB safety
            # net held, so answer 409 like any other availability conflict.
            self.rental_repo.rollback()
            logger.warning(
                "rejected rental for car %s: concurrent active rental", car_id
            )
            raise CarNotAvailableError(
                f"Car {car_id} is not available (already has an active rental)"
            )
        RENTALS_CREATED.inc()
        ONGOING_RENTALS.set(self.rental_repo.count_active())
        set_cars_gauge(self.car_repo.count_by_status())
        logger.info("rental %s created for car %s (customer=%s)", rental.id, car.id, customer_name)

        self._publish(
            "rental.created",
            {"rental_id": rental.id, "car_id": car.id, "customer": customer_name},
        )
        return rental

    def end_rental(self, rental_id: int) -> Rental:
        rental = self.rental_repo.get(rental_id)
        if rental is None:
            raise RentalNotFoundError(f"Rental {rental_id} not found")
        if rental.end_date is not None:
            logger.warning("rejected end of rental %s: already ended", rental_id)
            raise RentalAlreadyEndedError(f"Rental {rental_id} has already ended")

        self.rental_repo.end(rental)
        car = self.car_repo.get(rental.car_id)
        self.car_repo.update_status(car, CarStatus.AVAILABLE)
        self.rental_repo.commit()
        ONGOING_RENTALS.set(self.rental_repo.count_active())
        set_cars_gauge(self.car_repo.count_by_status())
        logger.info("rental %s ended for car %s", rental.id, car.id)

        self._publish("rental.ended", {"rental_id": rental.id, "car_id": car.id})
        return rental

    def list_rentals(self, active: Optional[bool] = None) -> list[Rental]:
        rentals = self.rental_repo.list(active=active)
        logger.debug("list_rentals returned %d rental(s) (active=%s)", len(rentals), active)
        return rentals

    def _publish(self, routing_key: str, body: dict) -> None:
        if self.publisher is not None:
            self.publisher.publish(routing_key, body)
