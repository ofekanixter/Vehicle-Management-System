def test_register_and_end_rental_flow(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()

    rental_response = client.post(
        "/rentals", json={"car_id": car["id"], "customer_name": "Ofek"}
    )
    assert rental_response.status_code == 201
    rental = rental_response.json()
    assert rental["end_date"] is None
    assert client.get(f"/cars/{car['id']}").json()["status"] == "rented"

    end_response = client.post(f"/rentals/{rental['id']}/end")
    assert end_response.status_code == 200
    assert end_response.json()["end_date"] is not None
    assert client.get(f"/cars/{car['id']}").json()["status"] == "available"


def test_rent_unavailable_car_returns_409(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()
    client.post("/rentals", json={"car_id": car["id"], "customer_name": "Ofek"})

    response = client.post(
        "/rentals", json={"car_id": car["id"], "customer_name": "Dana"}
    )

    assert response.status_code == 409


def test_register_rental_unknown_car_returns_404(client):
    response = client.post(
        "/rentals", json={"car_id": 999999, "customer_name": "Ofek"}
    )

    assert response.status_code == 404
