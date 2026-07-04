import logging

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

logger = logging.getLogger(__name__)

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
        logger.debug("mapped %s to 404: %s", type(exc).__name__, exc)
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    def conflict(request: Request, exc: Exception) -> JSONResponse:
        logger.debug("mapped %s to 409: %s", type(exc).__name__, exc)
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    def unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    for exc_class in NOT_FOUND_ERRORS:
        app.add_exception_handler(exc_class, not_found)
    for exc_class in CONFLICT_ERRORS:
        app.add_exception_handler(exc_class, conflict)
    app.add_exception_handler(Exception, unhandled)
