import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.exception_handlers import register_exception_handlers
from app.api.routers import cars, health, rentals
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging
from app.models.models import Car, Rental

setup_logging(logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables automatically on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(cars.router)
app.include_router(rentals.router)
register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} Vehicle Management System API"}
