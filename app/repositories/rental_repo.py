from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Rental


class RentalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, car_id: int, customer_name: str) -> Rental:
        rental = Rental(car_id=car_id, customer_name=customer_name)
        self.session.add(rental)
        self.session.flush()
        return rental

    def get(self, rental_id: int) -> Optional[Rental]:
        return self.session.get(Rental, rental_id)

    def get_active_for_car(self, car_id: int) -> Optional[Rental]:
        return (
            self.session.query(Rental)
            .filter(Rental.car_id == car_id, Rental.end_date.is_(None))
            .first()
        )

    def list(self, active: Optional[bool] = None) -> list[Rental]:
        query = self.session.query(Rental)
        if active is True:
            query = query.filter(Rental.end_date.is_(None))
        elif active is False:
            query = query.filter(Rental.end_date.isnot(None))
        return query.all()

    def end(self, rental: Rental) -> Rental:
        rental.end_date = datetime.now(timezone.utc)
        self.session.flush()
        return rental

    def commit(self) -> None:
        self.session.commit()
