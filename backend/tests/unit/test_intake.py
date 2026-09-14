import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ExternalAPIError, MovieAlreadyExistsError, MovieNotFoundError
from app.models.genre import Genre
from app.models.movie import Movie
from app.services.intake import IntakeService


@pytest.fixture
def mock_tmdb(mocker):
    client = mocker.MagicMock()
    client.find_by_imdb_id = mocker.AsyncMock()
    client.get_popular = mocker.AsyncMock(return_value=[])
    client.get_movie_details = mocker.AsyncMock(return_value={})
    client.get_genre_map = mocker.AsyncMock(return_value={})
    client.get_poster_url = mocker.MagicMock(return_value="https://image.tmdb.org/t/p/w500/poster.jpg")
    return client


@pytest.fixture
def mock_db(mocker):
    session = mocker.AsyncMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value = []
    session.execute.return_value = mock_result
    return session


def _find_payload(**overrides):
    payload = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
        "genre_ids": [18],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_import_by_imdb(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.return_value = _find_payload()

    service = IntakeService(mock_db, mock_tmdb)
    movie = await service.import_by_imdb("tt0137566")

    assert movie.tmdb_id == 550
    assert movie.imdb_id == "tt0137566"
    assert movie.title == "Fight Club"
    assert movie.rating == 8.4
    assert movie.genres is None  # genre cache empty
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_import_maps_genre_ids_through_cache(mock_db, mock_tmdb, mocker):
    mock_tmdb.find_by_imdb_id.return_value = _find_payload()
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value = [Genre(id=18, name="Drama")]
    mock_db.execute.return_value = mock_result

    service = IntakeService(mock_db, mock_tmdb)
    movie = await service.import_by_imdb("tt0137566")

    assert movie.genres == ["Drama"]


@pytest.mark.asyncio
async def test_import_tolerates_bad_date(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.return_value = _find_payload(release_date="not-a-date")

    service = IntakeService(mock_db, mock_tmdb)
    movie = await service.import_by_imdb("tt0137566")

    assert movie.release_date is None


@pytest.mark.asyncio
async def test_import_movie_already_exists_by_imdb(mock_db, mock_tmdb, mocker):
    existing = mocker.MagicMock(spec=Movie)
    existing.tmdb_id = 550
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute.return_value = mock_result

    service = IntakeService(mock_db, mock_tmdb)
    with pytest.raises(MovieAlreadyExistsError):
        await service.import_by_imdb("tt0137566")

    mock_tmdb.find_by_imdb_id.assert_not_called()


@pytest.mark.asyncio
async def test_import_movie_not_found_on_tmdb(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.return_value = None

    service = IntakeService(mock_db, mock_tmdb)
    with pytest.raises(MovieNotFoundError):
        await service.import_by_imdb("tt9999999")


@pytest.mark.asyncio
async def test_import_movie_tmdb_api_error(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.side_effect = ExternalAPIError("TMDB", "timeout")

    service = IntakeService(mock_db, mock_tmdb)
    with pytest.raises(ExternalAPIError):
        await service.import_by_imdb("tt0137566")


@pytest.mark.asyncio
async def test_sync_popular_skips_existing(mock_db, mock_tmdb, mocker):
    mock_tmdb.get_popular.return_value = [{"id": 550, "title": "Fight Club"}]
    existing = mocker.MagicMock(spec=Movie)
    genre_result = mocker.MagicMock()
    genre_result.scalars.return_value = []
    hit_result = mocker.MagicMock()
    hit_result.scalar_one_or_none.return_value = existing
    mock_db.execute.side_effect = [genre_result, hit_result]

    service = IntakeService(mock_db, mock_tmdb)
    movies = await service.sync_popular()

    assert movies == []
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_sync_popular_genres_and_bad_date(mock_db, mock_tmdb, mocker):
    mock_tmdb.get_popular.return_value = [
        {
            "id": 550,
            "title": "Fight Club",
            "overview": "An insomniac office worker...",
            "release_date": "garbage",
            "vote_average": 8.4,
            "poster_path": "/poster.jpg",
            "genre_ids": [28],
        }
    ]
    genre_result = mocker.MagicMock()
    genre_result.scalars.return_value = [Genre(id=28, name="Action")]
    miss_result = mocker.MagicMock()
    miss_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [genre_result, miss_result]

    service = IntakeService(mock_db, mock_tmdb)
    movies = await service.sync_popular()

    assert len(movies) == 1
    assert movies[0].genres == ["Action"]
    assert movies[0].release_date is None


@pytest.mark.asyncio
async def test_backfill_imdb_fills_missing(mock_db, mock_tmdb, mocker):
    mock_tmdb.get_movie_details.return_value = {
        "external_ids": {"imdb_id": "tt0137566"}
    }
    movie = mocker.MagicMock(spec=Movie)
    movie.imdb_id = None
    movie.tmdb_id = 550

    service = IntakeService(mock_db, mock_tmdb)
    assert await service.backfill_imdb(movie) is True
    assert movie.imdb_id == "tt0137566"


@pytest.mark.asyncio
async def test_backfill_imdb_skips_when_set(mock_db, mock_tmdb, mocker):
    movie = mocker.MagicMock(spec=Movie)
    movie.imdb_id = "tt0137566"

    service = IntakeService(mock_db, mock_tmdb)
    assert await service.backfill_imdb(movie) is False
    mock_tmdb.get_movie_details.assert_not_called()


@pytest.mark.asyncio
async def test_sync_imdb_ids_fills_missing(mock_db, mock_tmdb, mocker):
    movie = mocker.MagicMock(spec=Movie)
    movie.imdb_id = None
    movie.tmdb_id = 550
    count_result = mocker.MagicMock()
    count_result.scalar.return_value = 1
    rows_result = mocker.MagicMock()
    rows_result.scalars.return_value = [movie]
    mock_db.execute.side_effect = [count_result, rows_result]
    mock_tmdb.get_movie_details.return_value = {
        "external_ids": {"imdb_id": "tt0137566"}
    }

    service = IntakeService(mock_db, mock_tmdb)
    progress = mocker.AsyncMock()
    filled = await service.sync_imdb_ids(on_progress=progress)

    assert filled == 1
    assert movie.imdb_id == "tt0137566"
    progress.assert_called_once_with(1, 1)


@pytest.mark.asyncio
async def test_sync_imdb_ids_respects_limit(mock_db, mock_tmdb, mocker):
    movies = []
    for tmdb_id in (550, 551):
        movie = mocker.MagicMock(spec=Movie)
        movie.imdb_id = None
        movie.tmdb_id = tmdb_id
        movies.append(movie)
    count_result = mocker.MagicMock()
    count_result.scalar.return_value = 2
    rows_result = mocker.MagicMock()
    rows_result.scalars.return_value = [movies[0]]
    mock_db.execute.side_effect = [count_result, rows_result]
    mock_tmdb.get_movie_details.return_value = {
        "external_ids": {"imdb_id": "tt0137566"}
    }

    service = IntakeService(mock_db, mock_tmdb)
    filled = await service.sync_imdb_ids(limit=1)

    assert filled == 1
    assert movies[1].imdb_id is None


def test_imdb_sync_rate_budget():
    """40 rows/run paced at 10/s: worst case 40 upstream calls per run."""
    assert IntakeService.IMDB_SYNC_BATCH_LIMIT == 40
    assert IntakeService.IMDB_SYNC_MIN_INTERVAL == 0.1


@pytest.mark.asyncio
async def test_sync_genres_upserts_and_backfills(mock_db, mock_tmdb, mocker):
    mock_tmdb.get_genre_map.return_value = {28: "Action"}
    mock_tmdb.get_movie_details.return_value = {
        "genres": [{"id": 28, "name": "Action"}]
    }
    movie = mocker.MagicMock(spec=Movie)
    movie.genres = None
    movie.tmdb_id = 550

    empty = mocker.MagicMock()
    empty.scalars.return_value = []
    genreless = mocker.MagicMock()
    genreless.scalars.return_value = [movie]
    mock_db.execute.side_effect = [empty, genreless]

    service = IntakeService(mock_db, mock_tmdb)
    filled = await service.sync_genres()

    assert filled == 1
    assert movie.genres == ["Action"]
    added = [c.args[0] for c in mock_db.add.call_args_list]
    assert any(isinstance(g, Genre) and g.id == 28 for g in added)
