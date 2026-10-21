import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy import Uuid as DB_Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Measurement(Base):
    __tablename__ = "measurements"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    sensor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[float] = mapped_column(Float)


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id: Mapped[uuid.UUID] = mapped_column(DB_Uuid(as_uuid=True), primary_key=True, default=func.uuidv7())
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sensor_id: Mapped[str] = mapped_column(String(64))
    event: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(32))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[str] = mapped_column(String(16))
    ack_user: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ack_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
