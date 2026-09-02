from pydantic import BaseModel, ConfigDict


class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tmdb_id: int
    imdb_id: str | None = None
    title: str
    release_date: str | None = None
    rating: float | None = None
    poster_url: str | None = None


class MovieListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    imdb_id: str | None = None
    title: str
    release_date: str | None = None
    rating: float | None = None
    poster_url: str | None = None


class MovieDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    imdb_id: str | None = None
    title: str
    release_date: str | None = None
    synopsis: str | None = None
    genres: list[str] | None = None
    rating: float | None = None
    poster_url: str | None = None
    created_at: str
    updated_at: str


class MovieImportRequest(BaseModel):
    imdb_id: str


class PaginatedMovieResponse(BaseModel):
    movies: list[MovieListResponse]
    total: int
    page: int
    per_page: int
