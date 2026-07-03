class CarNotFoundError(Exception):
    pass


class RentalNotFoundError(Exception):
    pass


class CarNotAvailableError(Exception):
    pass


class CarHasActiveRentalError(Exception):
    pass


class CarHasRentalHistoryError(Exception):
    pass


class RentalAlreadyEndedError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass
