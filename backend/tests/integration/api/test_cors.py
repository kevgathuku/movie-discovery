"""CORS origins come from settings; unlisted origins get no ACAO header."""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_cors_allows_only_configured_origins(mocker):
    mocker.patch(
        "app.main.settings",
        mocker.MagicMock(
            CORS_ORIGINS="http://allowed.example",
            TMDB_API_KEY="x",
        ),
    )
    from app.main import create_app

    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as ac:
        ok = await ac.get(
            "/health", headers={"Origin": "http://allowed.example"}
        )
        assert ok.headers["access-control-allow-origin"] == (
            "http://allowed.example"
        )
        denied = await ac.get(
            "/health", headers={"Origin": "http://evil.example"}
        )
        assert "access-control-allow-origin" not in denied.headers
