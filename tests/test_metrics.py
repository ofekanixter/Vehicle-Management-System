def _metric_value(body, name, labels=""):
    prefix = f"{name}{labels} "
    for line in body.splitlines():
        if line.startswith(prefix):
            return float(line.split()[-1])
    return None


def test_metrics_endpoint_exposes_expected_series(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "drivenow_cars_total" in body
    assert "drivenow_ongoing_rentals" in body
    assert "drivenow_request_duration_seconds" in body
    assert "drivenow_rentals_created_total" in body


def test_creating_car_sets_available_gauge(client):
    client.post("/cars", json={"model": "Mazda 3", "year": 2022})

    body = client.get("/metrics").text

    assert _metric_value(body, "drivenow_cars_total", '{status="available"}') == 1.0


def test_registering_rental_updates_ongoing_and_created_metrics(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()
    created_before = _metric_value(
        client.get("/metrics").text,
        "drivenow_rentals_created_total",
    )

    client.post("/rentals", json={"car_id": car["id"], "customer_name": "Ofek"})

    body = client.get("/metrics").text
    assert _metric_value(body, "drivenow_ongoing_rentals") == 1.0
    assert _metric_value(body, "drivenow_cars_total", '{status="rented"}') == 1.0
    assert _metric_value(body, "drivenow_cars_total", '{status="available"}') == 0.0
    assert _metric_value(body, "drivenow_rentals_created_total") == created_before + 1


def test_ending_rental_decrements_ongoing_gauge(client):
    car = client.post("/cars", json={"model": "Mazda 3", "year": 2022}).json()
    rental = client.post(
        "/rentals", json={"car_id": car["id"], "customer_name": "Ofek"}
    ).json()

    client.post(f"/rentals/{rental['id']}/end")

    body = client.get("/metrics").text
    assert _metric_value(body, "drivenow_ongoing_rentals") == 0.0
    assert _metric_value(body, "drivenow_cars_total", '{status="available"}') == 1.0
