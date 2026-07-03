from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import (
    CarHasActiveRentalError,
    CarHasRentalHistoryError,
    CarNotAvailableError,
    CarNotFoundError,
    InvalidStatusTransitionError,
    RentalAlreadyEndedError,
    RentalNotFoundError,
)

NOT_FOUND_ERRORS = (CarNotFoundError, RentalNotFoundError)
CONFLICT_ERRORS = (
    CarNotAvailableError,
    CarHasActiveRentalError,
    CarHasRentalHistoryError,
    RentalAlreadyEndedError,
    InvalidStatusTransitionError,
)


def register_exception_handlers(app: FastAPI) -> None:
    def not_found(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    def conflict(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    for exc_class in NOT_FOUND_ERRORS:
        app.add_exception_handler(exc_class, not_found)
    for exc_class in CONFLICT_ERRORS:
        app.add_exception_handler(exc_class, conflict)
