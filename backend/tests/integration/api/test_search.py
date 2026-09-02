import pytest

from app.models.movie import Movie, MovieSource
from app.repositories.movie_repo import MovieRepository


async def _create_movie(session, tmdb_id, title):
    repo = MovieRepository(session)
    movie = Movie(
        tmdb_id=tmdb_id,
        title=title,
        source=MovieSource.sync,
    )
    return await repo.create(movie)


async def test_search_min_length_validation(client):
    response = await client.get("/api/v1/search", params={"q": "a"})
    assert response.status_code == 422


async def test_search_empty_database(client):
    response = await client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0
    assert data["suggestion"] == "No local results. Import from TMDB by IMDB ID."


async def test_search_returns_matching_movies(client, db_session):
    await _create_movie(db_session, 550, "Fight Club")
    await _create_movie(db_session, 680, "Pulp Fiction")
    await _create_movie(db_session, 13, "Forrest Gump")
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "fight"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "Fight Club"
    assert data["suggestion"] is None


async def test_search_case_insensitive(client, db_session):
    await _create_movie(db_session, 550, "Fight Club")
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "FIGHT"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


async def test_search_partial_match(client, db_session):
    await _create_movie(db_session, 550, "Fight Club")
    await _create_movie(db_session, 680, "The Fighting Pit")
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "fight"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


async def test_search_no_suggestion_when_results_exist(client, db_session):
    await _create_movie(db_session, 550, "Fight Club")
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "fight"})
    data = response.json()
    assert data["suggestion"] is None


async def test_search_pagination(client, db_session):
    for i in range(5):
        await _create_movie(db_session, 100 + i, f"Movie {i}")
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "movie", "per_page": 2, "page": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["per_page"] == 2
