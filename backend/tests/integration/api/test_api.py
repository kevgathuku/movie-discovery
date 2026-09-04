

async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_movies_empty(client):
    response = await client.get("/api/v1/movies")
    assert response.status_code == 200
    data = response.json()
    assert data["movies"] == []
    assert data["total"] == 0


async def test_search_movies_empty(client):
    response = await client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


async def test_list_watchlists_empty(client):
    response = await client.get("/api/v1/watchlists")
    assert response.status_code == 200
    data = response.json()
    assert data["watchlists"] == []


async def test_get_job_not_found(client):
    response = await client.get("/api/v1/jobs/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Not implemented yet"
