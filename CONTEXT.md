# Movie Discovery

A personal movie catalog with watchlists: movies are imported from TMDB into a local catalog, organised into per-user watchlists, and tracked from intention to watched.

## Language

### Catalog

**Movie**:
A film in the local catalog, keyed internally by `id` and externally by TMDB and IMDb identifiers.
_Avoid_: title (as an identifier), video, asset

**TMDB ID**:
The movie's identifier in The Movie Database; the canonical external key for import and sync.
_Avoid_: tmdbId, external id

**IMDb ID**:
The movie's `tt...` identifier; the intake key for single-movie import and the backfill key on detail view.
_Avoid_: imdbId

**Synopsis**:
The plot text stored on a movie.
_Avoid_: overview (TMDB's payload key — map it on intake, never persist the name)

**Rating**:
The movie's score as stored locally.
_Avoid_: vote_average (TMDB's payload key — map it on intake)

**Poster URL**:
The fully-qualified poster image URL stored on a movie.
_Avoid_: poster_path (TMDB's payload key — expand it on intake)

**Source**:
Where a catalog row came from: `manual` or `sync`.
_Avoid_: origin, provider

**Genre**:
A TMDB genre cached locally by TMDB id; the id→name map used to label movies on intake.
_Avoid_: genre_id (as a stored movie attribute — movies store names)

### Library

**Watchlist**:
A named collection of movies owned by one user.
_Avoid_: list, collection, queue

**Owner**:
The user a watchlist belongs to.
_Avoid_: user (as a foreign-key name — `owner_id` on watchlists)

**Watchlist entry**:
One movie's membership in one watchlist, carrying its own watch status. A movie appears at most once per watchlist.
_Avoid_: item, watchlist movie

**Watch status**:
An entry's state: `to_watch` or `watched`, with `watched_at` set on transition.
_Avoid_: state, seen, done

### Identity

**User**:
An account identified by email (case-insensitive).
_Avoid_: account, customer, client

**Admin**:
A user with the `admin` role; required for job inspection.
_Avoid_: superuser, moderator

### Background work

**Sync job**:
A record of one background catalog-sync run (`sync_popular`), from `queued` through `processing` to `completed` or `failed`.
_Avoid_: task (that's the Celery unit — the job is the durable record), cron job
