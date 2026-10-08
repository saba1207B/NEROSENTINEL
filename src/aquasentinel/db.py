from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from aquasentinel.config import get_settings


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class RegionModel(TimestampMixin, Base):
    __tablename__ = "regions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    region_type: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    area_km2: Mapped[float] = mapped_column(Float, nullable=False)
    centroid: Mapped[dict] = mapped_column(JSON, nullable=False)


class DataSourceModel(TimestampMixin, Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)


class ObservationModel(TimestampMixin, Base):
    __tablename__ = "observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    region_id: Mapped[str] = mapped_column(ForeignKey("regions.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    variable: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    region: Mapped[RegionModel] = relationship()
    __table_args__ = (Index("ix_observation_region_variable_time", "region_id", "variable", "observed_at"),)


class ScenarioModel(TimestampMixin, Base):
    __tablename__ = "scenarios"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    region_id: Mapped[str] = mapped_column(ForeignKey("regions.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON)


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

