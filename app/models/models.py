import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Enum,
    Index,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CarStatus(str, enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CarStatus] = mapped_column(
        Enum(CarStatus, name="car_status", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        default=CarStatus.AVAILABLE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    rentals: Mapped[List["Rental"]] = relationship(
        "Rental", back_populates="car"
    )

    __table_args__ = (CheckConstraint("year >= 1950", name="check_year_min"),)


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id"), nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    car: Mapped["Car"] = relationship("Car", back_populates="rentals")

    __table_args__ = (
        Index(
            "one_active_rental_per_car",
            "car_id",
            unique=True,
            postgresql_where=text("end_date IS NULL"),
        ),
    )
