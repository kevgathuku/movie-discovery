import httpx

from app.exceptions import ExternalAPIError


class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            params={"api_key": self.api_key},
            timeout=10.0,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = await self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ExternalAPIError(
                    "TMDB", "No movie found for the given identifier"
                ) from e
            raise ExternalAPIError(
                "TMDB", f"HTTP {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise ExternalAPIError(
                "TMDB", f"Request failed: {e}"
            ) from e

    async def search_movies(self, query: str) -> list[dict]:
        data = await self._request("GET", "/search/movie", params={"query": query})
        return data.get("results", [])

    async def get_movie_details(self, movie_id: int) -> dict:
        return await self._request("GET", f"/movie/{movie_id}")

    async def find_by_imdb_id(self, imdb_id: str) -> dict | None:
        data = await self._request(
            "GET", f"/find/{imdb_id}", params={"external_source": "imdb_id"}
        )
        results = data.get("movie_results", [])
        if not results:
            return None
        return results[0]

    async def get_movie_credits(self, movie_id: int) -> dict:
        return await self._request("GET", f"/movie/{movie_id}/credits")

    def get_poster_url(self, poster_path: str | None) -> str | None:
        if not poster_path:
            return None
        return f"{self.IMAGE_BASE_URL}{poster_path}"
