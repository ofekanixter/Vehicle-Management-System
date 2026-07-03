import pytest

from app.models.models import CarStatus
from app.services.exceptions import (
    CarNotAvailableError,
    CarNotFoundError,
    RentalAlreadyEndedError,
    RentalNotFoundError,
)


def test_register_rental_marks_car_rented(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)

    rental = rental_service.register_rental(car_id=car.id, customer_name="Ofek")

    assert rental.car_id == car.id
    assert rental.end_date is None
    assert car_service.get_car(car.id).status == CarStatus.RENTED


def test_cannot_rent_unavailable_car(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental_service.register_rental(car_id=car.id, customer_name="Ofek")

    with pytest.raises(CarNotAvailableError):
        rental_service.register_rental(car_id=car.id, customer_name="Dana")


def test_register_rental_unknown_car_raises(rental_service):
    with pytest.raises(CarNotFoundError):
        rental_service.register_rental(car_id=999_999, customer_name="Ofek")


def test_end_rental_frees_car(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental = rental_service.register_rental(car_id=car.id, customer_name="Ofek")

    ended = rental_service.end_rental(rental.id)

    assert ended.end_date is not None
    assert car_service.get_car(car.id).status == CarStatus.AVAILABLE


def test_cannot_end_already_ended_rental(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental = rental_service.register_rental(car_id=car.id, customer_name="Ofek")
    rental_service.end_rental(rental.id)

    with pytest.raises(RentalAlreadyEndedError):
        rental_service.end_rental(rental.id)


def test_end_unknown_rental_raises(rental_service):
    with pytest.raises(RentalNotFoundError):
        rental_service.end_rental(999_999)


def test_rental_created_event_published(car_service, rental_service, fake_publisher):
    car = car_service.add_car(model="Mazda 3", year=2022)

    rental = rental_service.register_rental(car_id=car.id, customer_name="Ofek")

    assert (
        "rental.created",
        {"rental_id": rental.id, "car_id": car.id, "customer": "Ofek"},
    ) in fake_publisher.events


def test_rental_ended_event_published(car_service, rental_service, fake_publisher):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental = rental_service.register_rental(car_id=car.id, customer_name="Ofek")

    rental_service.end_rental(rental.id)

    assert ("rental.ended", {"rental_id": rental.id, "car_id": car.id}) in fake_publisher.events
