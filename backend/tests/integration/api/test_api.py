

async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_movies_response_shape(client):
    """List movies must return paginated envelope even when empty."""
    response = await client.get("/api/v1/movies")
    assert response.status_code == 200
    data = response.json()
    assert data["movies"] == []
    assert data["total"] == 0
    assert "page" in data
    assert "per_page" in data


async def test_list_movies_pagination_params(client):
    """Pagination params must be respected."""
    response = await client.get("/api/v1/movies", params={"page": 2, "per_page": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["per_page"] == 5


async def test_search_empty_query(client):
    """Empty search must return empty results, not error."""
    response = await client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0
    assert "suggestion" in data


async def test_list_watchlists_response_shape(client, make_user_headers):
    """Watchlists response must contain the list envelope."""
    headers = await make_user_headers("owner@example.com")
    response = await client.get("/api/v1/watchlists", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "watchlists" in data
    assert isinstance(data["watchlists"], list)


async def test_get_job_not_found(client):
    # Public jobs stub removed in 002-user-auth US4; jobs live under /admin.
    response = await client.get("/api/v1/jobs/nonexistent")
    assert response.status_code == 404
