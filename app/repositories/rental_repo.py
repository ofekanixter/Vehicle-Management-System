import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Rental

logger = logging.getLogger(__name__)


class RentalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, car_id: int, customer_name: str) -> Rental:
        rental = Rental(car_id=car_id, customer_name=customer_name)
        self.session.add(rental)
        self.session.flush()
        logger.debug("rental %s flushed for car %s (pending commit)", rental.id, car_id)
        return rental

    def get(self, rental_id: int) -> Optional[Rental]:
        rental = self.session.get(Rental, rental_id)
        logger.debug("rental %s lookup: %s", rental_id, "found" if rental else "not found")
        return rental

    def get_active_for_car(self, car_id: int) -> Optional[Rental]:
        rental = (
            self.session.query(Rental)
            .filter(Rental.car_id == car_id, Rental.end_date.is_(None))
            .first()
        )
        logger.debug("active rental lookup for car %s: %s", car_id, "found" if rental else "not found")
        return rental

    def list(self, active: Optional[bool] = None) -> list[Rental]:
        query = self.session.query(Rental)
        if active is True:
            query = query.filter(Rental.end_date.is_(None))
        elif active is False:
            query = query.filter(Rental.end_date.isnot(None))
        rentals = query.all()
        logger.debug("rental query returned %d rental(s) (active=%s)", len(rentals), active)
        return rentals

    def count_active(self) -> int:
        count = self.session.query(Rental).filter(Rental.end_date.is_(None)).count()
        logger.debug("active rental count: %d", count)
        return count

    def count_all(self) -> int:
        count = self.session.query(Rental).count()
        logger.debug("total rental count: %d", count)
        return count

    def end(self, rental: Rental) -> Rental:
        rental.end_date = datetime.now(timezone.utc)
        self.session.flush()
        logger.debug("rental %s end_date flushed (pending commit)", rental.id)
        return rental

    def commit(self) -> None:
        self.session.commit()
        logger.debug("transaction committed")

    def rollback(self) -> None:
        self.session.rollback()
        logger.debug("transaction rolled back")
