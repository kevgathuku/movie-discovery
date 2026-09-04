import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.movie import Movie


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    entries: Mapped[list[WatchlistEntry]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistStatus(enum.StrEnum):
    to_watch = "to_watch"
    watched = "watched"


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[WatchlistStatus] = mapped_column(
        nullable=False, default=WatchlistStatus.to_watch
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    watched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    watchlist: Mapped[Watchlist] = relationship(back_populates="entries")
    movie: Mapped[Movie] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "watchlist_id",
            "movie_id",
            name="uq_watchlist_entries_watchlist_movie",
        ),
    )
