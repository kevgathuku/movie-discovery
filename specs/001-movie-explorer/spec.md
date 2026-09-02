# Movie Explorer

## Overview

Movie Explorer is a full-stack web application that allows users to discover movies, search for movies using The Movie Database (TMDB), import selected movie metadata into a local database, and manage a personal watchlist.

## Clarifications

### Session 2026-09-02

- Q: Should search check the local database first or TMDB first? → A: Local database first; TMDB is a fallback for missing content.
- Q: When local search returns no results? → A: User is offered the option to import a movie from TMDB by IMDB ID as a fallback.
- Q: Should the home page (movie discovery) work offline or require an internet connection? → A: Home page works offline using a local cache of trending/popular movies, kept current by a background service that periodically syncs from TMDB.
- Q: What primary key types should the entities use? → A: Movie and WatchlistEntry use BIGINT auto-increment. Job uses Sqids-generated short string IDs (sqids.org/python).

## User Scenarios & Testing

### Primary User Scenarios

1. **Discover Movies**: A user visits the application and browses a curated display of popular, trending, and recommended movies without needing to search.

2. **Search for Movies**: A user enters a movie title (or partial title) into a search bar and first sees matching results from the local database. If no local results are found, the user can import a movie from TMDB by entering its IMDB ID.

3. **View Movie Details**: A user selects a movie from discovery or search results to view its full metadata — title, release date, synopsis, genres, rating, and cast.

4. **Import Movie to Local Database**: A user selects a movie from search results and imports its full metadata into the local database for offline access and watchlist management.

5. **Add Movie to Watchlist**: A user adds an imported movie to their personal watchlist to track films they intend to watch.

6. **Manage Watchlist**: A user views their watchlist, marks movies as watched, removes movies, and sorts/filters the list.

7. **Remove Movie from Local Database**: A user removes a movie's metadata from the local database when it is no longer needed.

### Acceptance Scenarios

- **Given** a user is on the home page, **When** they load the page, **Then** they see a display of popular/trending movies.
- **Given** a user types a movie title in the search bar, **When** they submit the search, **Then** they first see matching results from the local database.
- **Given** a user searches and the local database has no matching movies, **When** no local results are found, **Then** the user is prompted to import from TMDB by entering an IMDB ID.
- **Given** a user enters an IMDB ID in the fallback import flow, **When** they confirm, **Then** the movie metadata is fetched from TMDB and saved to the local database.
- **Given** a user views a movie's details, **When** they click "Import", **Then** the movie's metadata is saved to the local database and confirmed to the user.
- **Given** a user has imported movies, **When** they click "Add to Watchlist", **Then** the movie appears in their watchlist.
- **Given** a user is on their watchlist page, **When** they mark a movie as watched, **Then** the movie's status updates to "watched" and remains visible in the list.
- **Given** a user is on their watchlist page, **When** they remove a movie, **Then** the movie is removed from the watchlist but its metadata remains in the local database.
- **Given** a user has imported movies, **When** they choose to remove a movie from the local database, **Then** the movie and its associated watchlist entry are deleted.

### Edge Cases

- TMDB API is unavailable or returns an error — user sees a friendly error message and can retry.
- A user searches for a movie that does not exist in either the local database or TMDB — user sees a "no results found" message.
- A user tries to import a movie that is already in the local database — user is informed the movie already exists.
- A user tries to add a movie to the watchlist that is already in it — user is informed it is already on their watchlist.
- Network timeout during TMDB fallback import — user is prompted to check their connection and retry.
- User enters an invalid IMDB ID — user sees a "movie not found" message and can retry.

## Requirements

### Functional Requirements

**Discovery**
- R1: The application displays a home page with popular/trending movies sourced from the local database.
- R2: Movie listings on the home page include the movie poster, title, and release year.
- R3: A background service periodically syncs popular/trending movies from TMDB into the local database to keep discovery content current.

**Search**
- R4: Users can search for movies by title using a search input.
- R5: Search queries against the local database return matching movies displaying the poster, title, and release year.
- R6: When local search returns no results, the user is offered the option to import a movie from TMDB by entering an IMDB ID.
- R7: Users can import a movie into the local database by providing an IMDB ID, which fetches metadata from TMDB.
- R8: Search results update as the user types (debounced) or upon pressing Enter. *(debounce is frontend responsibility — backend search endpoint is stateless)*
- R9: The application handles empty search queries gracefully by showing no results.

**Movie Details**
- R10: Users can select a movie to view detailed metadata including title, release date, synopsis, genres, rating, and cast.
- R11: Movie details are fetched from TMDB in real time when a user views a movie not yet imported locally. *(deferred to post-MVP — import flow satisfies core use case)*

**Local Database Import**
- R12: Users can import a movie's full metadata from TMDB into the local database.
- R13: Imported movies are stored with all relevant metadata fields (title, release date, synopsis, genres, rating, poster URL, TMDB ID, IMDB ID).
- R14: The application prevents duplicate imports of the same movie (matched by TMDB ID).
- R15: Users can remove a movie's metadata from the local database.

**Watchlist Management**
- R16: Users can create multiple named watchlists (e.g., "To Watch", "Watched", "Upcoming").
- R17: Users can add an imported movie to a specific watchlist.
- R18: Users can view all movies in a selected watchlist.
- R19: Users can mark a watchlist entry as "watched".
- R20: Users can remove a movie from a watchlist without deleting its local database entry.
- R21: Users can sort or filter a watchlist (e.g., by date added, title, or watched status).
- R22: Users can rename or delete a watchlist (entries are removed with the watchlist).

**General**
- R23: The application provides clear feedback for all user actions (success, error, loading states).
- R24: The application handles network errors gracefully with user-friendly messages.

### Non-Functional Requirements

- R25: Local search results are displayed to the user within 1 second.
- R26: TMDB fallback import by IMDB ID completes within 3 seconds under normal network conditions.
- R27: The background sync service keeps trending/popular movie data current (no more than 24 hours stale).
- R28: The application works in modern web browsers without requiring plugins or special configuration.
- R29: The user interface is responsive and usable on desktop and tablet screen sizes. *(frontend scope — deferred with skeleton in T042)*

## Success Criteria

- Users can discover trending movies on the home page without performing any search.
- Users can find any movie by title through the local database search, with TMDB fallback for movies not yet imported.
- Users can import movie metadata into the local database for persistent access.
- Users can maintain a personal watchlist and track which movies they have watched.
- The application handles TMDB API failures gracefully without crashing.
- Users can complete a full flow (search → import → add to watchlist → mark as watched) in under 5 minutes.
- 90% of search queries return results within 3 seconds.

## Key Entities

- **Movie**: Represents a film with metadata including title, release date, synopsis, genres, rating, poster URL, a unique TMDB identifier, and an IMDB identifier.
- **Watchlist**: A named collection of movies (e.g., "To Watch", "Watched", "Upcoming"). Users can create multiple watchlists.
- **Watchlist Entry**: Represents a movie in a specific watchlist, with a status (to-watch or watched) and a date added.
- **Local Movie Record**: A movie whose metadata has been imported from TMDB and stored locally for offline access and watchlist association.

## Assumptions

- The application uses TMDB as the sole external movie data source.
- There is a single user (no multi-user authentication system in this version).
- TMDB API access is available and a valid API key is configured.
- The local database requires no external server or network setup to operate.
- Movie metadata is imported on-demand per movie, not bulk-imported.
- Search always checks the local database first; TMDB is used only as a fallback when local results are empty.
- A background service periodically syncs trending/popular movies from TMDB into the local database.
- The watchlist is local to the user's instance of the application (not synced across devices).

## Scope

### In Scope

- Movie discovery (home page with trending/popular movies from local database)
- Background sync service for trending/popular movies from TMDB
- Movie search (local database first, TMDB fallback)
- Movie detail view
- Individual movie metadata import to local database
- Personal watchlist (add, remove, mark as watched, sort/filter)
- Removal of movie metadata from local database
- Error handling for API failures and network issues

### Out of Scope

- User authentication and multi-user support
- Social features (sharing, reviews, ratings by users)
- Movie recommendations based on watch history
- Offline search limitations (local database search works offline; TMDB fallback requires internet)
- Video playback or trailer streaming
- Mobile native applications
- Bulk import of movies
- Cross-device watchlist synchronization
