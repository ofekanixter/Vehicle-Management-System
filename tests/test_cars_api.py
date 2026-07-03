def test_create_car_returns_201(client):
    response = client.post("/cars", json={"model": "Mazda 3", "year": 2022})

    assert response.status_code == 201
    body = response.json()
    assert body["model"] == "Mazda 3"
    assert body["status"] == "available"


def test_create_car_invalid_year_returns_422(client):
    response = client.post("/cars", json={"model": "Mazda 3", "year": 1900})

    assert response.status_code == 422


def test_get_unknown_car_returns_404(client):
    response = client.get("/cars/999999")

    assert response.status_code == 404


def test_free_rented_car_via_patch_returns_409(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()
    client.post("/rentals", json={"car_id": car["id"], "customer_name": "Ofek"})

    response = client.patch(f"/cars/{car['id']}", json={"status": "available"})

    assert response.status_code == 409
    assert client.get(f"/cars/{car['id']}").json()["status"] == "rented"


def test_delete_car_with_rental_returns_409(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()
    client.post("/rentals", json={"car_id": car["id"], "customer_name": "Ofek"})

    response = client.delete(f"/cars/{car['id']}")

    assert response.status_code == 409
