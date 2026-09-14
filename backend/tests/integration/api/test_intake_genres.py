import pytest
from sqlalchemy import select, text

from app.models.movie import Movie, MovieSource
from app.services.intake import IntakeService


@pytest.mark.asyncio
async def test_sync_genres_backfills_json_null_rows(db_session, mocker):
    """Legacy rows holding the JSON literal null must be repaired, not skipped."""
    await db_session.execute(
        text(
            "INSERT INTO movies (tmdb_id, title, genres, source) "
            "VALUES (550, 'Fight Club', 'null', 'sync')"
        )
    )
    await db_session.commit()

    mock_tmdb = mocker.MagicMock()
    mock_tmdb.get_genre_map = mocker.AsyncMock(return_value={18: "Drama"})
    mock_tmdb.get_movie_details = mocker.AsyncMock(
        return_value={"genres": [{"id": 18, "name": "Drama"}]}
    )

    filled = await IntakeService(db_session, mock_tmdb).sync_genres()
    await db_session.commit()

    assert filled == 1
    movie = (
        await db_session.execute(select(Movie).where(Movie.tmdb_id == 550))
    ).scalar_one()
    assert movie.genres == ["Drama"]
    assert movie.source == MovieSource.sync


@pytest.mark.asyncio
async def test_sync_imdb_ids_fills_missing_row(db_session, mocker):
    db_session.add(Movie(tmdb_id=550, title="Fight Club", source=MovieSource.sync))
    await db_session.commit()

    mock_tmdb = mocker.MagicMock()
    mock_tmdb.get_movie_details = mocker.AsyncMock(
        return_value={"external_ids": {"imdb_id": "tt0137566"}}
    )

    filled = await IntakeService(db_session, mock_tmdb).sync_imdb_ids()
    await db_session.commit()

    assert filled == 1
    movie = (
        await db_session.execute(select(Movie).where(Movie.tmdb_id == 550))
    ).scalar_one()
    assert movie.imdb_id == "tt0137566"
