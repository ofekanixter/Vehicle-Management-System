from prometheus_client import Counter, Gauge, Histogram

CARS_BY_STATUS = Gauge("drivenow_cars_total", "Cars by status", ["status"])
ONGOING_RENTALS = Gauge("drivenow_ongoing_rentals", "Rentals currently active")
REQUEST_DURATION = Histogram(
    "drivenow_request_duration_seconds", "HTTP request latency", ["method", "path"]
)
RENTALS_CREATED = Counter("drivenow_rentals_created_total", "Rentals ever created")


def set_cars_gauge(counts_by_status: dict) -> None:
    for status_value, count in counts_by_status.items():
        CARS_BY_STATUS.labels(status=status_value).set(count)
