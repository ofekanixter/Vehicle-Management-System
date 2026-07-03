import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.exception_handlers import register_exception_handlers
from app.api.routers import cars, health, rentals
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging_config import setup_logging
from app.core.metrics import ONGOING_RENTALS, RENTALS_CREATED, REQUEST_DURATION, set_cars_gauge
from app.models.models import Car, Rental
from app.repositories.car_repo import CarRepository
from app.repositories.rental_repo import RentalRepository

setup_logging(logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables automatically on startup
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        set_cars_gauge(CarRepository(db).count_by_status())
        rental_repo = RentalRepository(db)
        ONGOING_RENTALS.set(rental_repo.count_active())
        RENTALS_CREATED.inc(rental_repo.count_all())
    finally:
        db.close()

    yield


# DEBUG only controls log verbosity (see setup_logging above). It is
# deliberately NOT passed to FastAPI(debug=...): that would swap in
# Starlette's debug middleware, which returns raw tracebacks to HTTP
# clients instead of the clean JSON 500 from our exception handler.
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(cars.router)
app.include_router(rentals.router)
register_exception_handlers(app)


@app.get("/metrics", tags=["Monitoring"])
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    metric_path = route.path if route is not None else request.url.path
    REQUEST_DURATION.labels(request.method, metric_path).observe(duration)

    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration * 1000,
    )
    return response


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} Vehicle Management System API"}
