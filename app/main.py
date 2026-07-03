from fastapi import FastAPI
from app.api.routers import health
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
)

app.include_router(health.router)

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} Vehicle Management System API"}
