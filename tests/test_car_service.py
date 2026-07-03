import pytest

from app.models.models import CarStatus
from app.services.exceptions import (
    CarHasRentalHistoryError,
    CarNotFoundError,
    InvalidStatusTransitionError,
)


def test_add_car_default_status_available(car_service):
    car = car_service.add_car(model="Mazda 3", year=2022)

    assert car.id is not None
    assert car.status == CarStatus.AVAILABLE


def test_list_cars_filter_by_status(car_service, rental_service):
    available_car = car_service.add_car(model="Mazda 3", year=2022)
    rented_car = car_service.add_car(model="Civic", year=2021)
    rental_service.register_rental(car_id=rented_car.id, customer_name="Dana")

    available = car_service.list_cars(status=CarStatus.AVAILABLE)
    rented = car_service.list_cars(status=CarStatus.RENTED)

    assert [c.id for c in available] == [available_car.id]
    assert [c.id for c in rented] == [rented_car.id]


def test_get_car_not_found_raises(car_service):
    with pytest.raises(CarNotFoundError):
        car_service.get_car(999_999)


def test_cannot_delete_car_with_active_rental(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental_service.register_rental(car_id=car.id, customer_name="Dana")

    with pytest.raises(CarHasRentalHistoryError):
        car_service.delete_car(car.id)


def test_cannot_delete_car_with_ended_rental_history(car_service, rental_service):
    car = car_service.add_car(model="Mazda 3", year=2022)
    rental = rental_service.register_rental(car_id=car.id, customer_name="Dana")
    rental_service.end_rental(rental.id)

    with pytest.raises(CarHasRentalHistoryError):
        car_service.delete_car(car.id)


def test_cannot_set_status_to_rented_directly(car_service):
    car = car_service.add_car(model="Mazda 3", year=2022)

    with pytest.raises(InvalidStatusTransitionError):
        car_service.update_status(car.id, CarStatus.RENTED)
