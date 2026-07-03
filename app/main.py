from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routers import health
from app.core.config import settings
from app.core.database import Base, engine
from app.models.models import Car, Rental


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


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} Vehicle Management System API"}
