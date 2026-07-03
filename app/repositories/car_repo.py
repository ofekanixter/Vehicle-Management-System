from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Car, CarStatus, Rental


class CarRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, model: str, year: int) -> Car:
        car = Car(model=model, year=year)
        self.session.add(car)
        self.session.flush()
        return car

    def get(self, car_id: int) -> Optional[Car]:
        return self.session.get(Car, car_id)

    def list(self, status: Optional[CarStatus] = None) -> list[Car]:
        query = self.session.query(Car)
        if status is not None:
            query = query.filter(Car.status == status)
        return query.all()

    def update_status(self, car: Car, status: CarStatus) -> Car:
        car.status = status
        self.session.flush()
        return car

    def has_rentals(self, car_id: int) -> bool:
        return (
            self.session.query(Rental.id).filter(Rental.car_id == car_id).first()
            is not None
        )

    def delete(self, car: Car) -> None:
        self.session.delete(car)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()
