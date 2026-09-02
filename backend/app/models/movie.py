import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class MovieSource(enum.StrEnum):
    manual = "manual"
    sync = "sync"


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    release_date: Mapped[date | None] = mapped_column(nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    genres: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[MovieSource] = mapped_column(
        nullable=False, default=MovieSource.manual
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

    __table_args__ = (
        Index("ix_movies_tmdb_id", "tmdb_id", unique=True),
        Index(
            "ix_movies_imdb_id",
            "imdb_id",
            unique=True,
            postgresql_where="imdb_id IS NOT NULL",
        ),
        Index("ix_movies_title", "title"),
        Index("ix_movies_source", "source"),
    )
