class MovieNotFoundError(Exception):
    def __init__(self, identifier: str | int) -> None:
        self.identifier = identifier
        super().__init__(f"Movie not found: {identifier}")


class MovieAlreadyExistsError(Exception):
    def __init__(self, tmdb_id: int) -> None:
        self.tmdb_id = tmdb_id
        super().__init__(f"Movie already exists with tmdb_id: {tmdb_id}")


class WatchlistNotFoundError(Exception):
    def __init__(self, watchlist_id: int) -> None:
        self.watchlist_id = watchlist_id
        super().__init__(f"Watchlist not found: {watchlist_id}")


class WatchlistEntryNotFoundError(Exception):
    def __init__(self, entry_id: int) -> None:
        self.entry_id = entry_id
        super().__init__(f"Watchlist entry not found: {entry_id}")


class WatchlistDuplicateError(Exception):
    def __init__(self, watchlist_id: int, movie_id: int) -> None:
        self.watchlist_id = watchlist_id
        self.movie_id = movie_id
        super().__init__(f"Movie {movie_id} already in watchlist {watchlist_id}")


class JobNotFoundError(Exception):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class ExternalAPIError(Exception):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        self.message = message
        super().__init__(f"External API error ({service}): {message}")
