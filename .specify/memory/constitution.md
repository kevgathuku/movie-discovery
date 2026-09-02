<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0 (MINOR: new principles added)
Modified principles: None renamed
Added principles:
  VI. Persistence Isolation
  VII. External API Isolation
  VIII. Asynchronous Work
  IX. Idempotency
  X. Reliable Background Jobs
  XI. Configuration and Secrets
  XII. Docker as the Development Environment
  XIII. Database Migrations
  XIV. API Contracts
Added sections: None
Removed sections: Containerized Development (superseded by Principle XII)
Follow-up TODOs: None
-->

# Movie Discovery Constitution

## Core Principles

### I. Architectural Boundaries

The system MUST maintain explicit separation between three primary layers:

- **API / HTTP** → **Services / Business Logic** → **Repositories / Persistence** → **Database**

External integrations follow a separate boundary:

- **Services** → **External API Clients** → **External Services**

Asynchronous processing follows:

- **API** → **Task Queue** → **Background Worker** → **Services**

Responsibilities MUST NOT leak across these boundaries without a documented reason. Each layer communicates only with its immediate neighbor through defined interfaces.

### II. Thin API Layer

FastAPI routes MUST remain thin. Routes are responsible for:

- HTTP request handling
- Input/output schema validation
- Dependency injection
- HTTP status codes
- Mapping domain errors to HTTP responses

Routes MUST NOT contain:

- Business rules
- SQLAlchemy queries
- Direct database manipulation
- Direct calls to external APIs (e.g., TMDB)
- Long-running operations
- Background job implementation

A route should generally delegate meaningful work to a service.

### III. Business Logic in Services

Business rules MUST live in services rather than API routes, repositories, or background task definitions.

Services SHOULD:

- Coordinate application workflows
- Enforce business rules
- Coordinate repositories
- Coordinate external clients
- Return domain/application objects
- Raise domain-specific exceptions

Services MUST NOT depend on FastAPI-specific HTTP concepts. In particular, business logic MUST NOT raise `HTTPException`. HTTP-specific error translation belongs at the API boundary.

### IV. Replaceable External Integrations

External integrations (e.g., TMDB API) MUST be isolated behind client interfaces defined in the services layer. This ensures:

- External services can be replaced without changing business logic
- External API clients can be mocked or stubbed in tests
- Failures in external services are handled at the client boundary, not propagated into business rules

### V. Reliable Asynchronous Processing

Long-running or background operations MUST be processed through a task queue and background worker, not within the API request cycle. The API layer enqueues work; the background worker executes it using the same service layer that synchronous code uses. This ensures:

- HTTP request handlers remain responsive
- Business logic is testable independently of the execution model
- Failed tasks can be retried without user intervention

### VI. Persistence Isolation

Database access MUST be isolated behind repositories. Repositories are responsible for:

- Queries
- Inserts
- Updates
- Deletes
- Database-specific persistence operations

Repositories MUST NOT:

- Call external APIs
- Contain HTTP concerns
- Enqueue background jobs
- Implement application workflows

Services should depend on repository abstractions rather than embedding SQLAlchemy queries throughout business logic.

### VII. External API Isolation

All communication with TMDB MUST occur through a dedicated client. Application code MUST NOT construct TMDB HTTP requests directly outside the TMDB client.

The TMDB client is responsible for:

- Authentication
- HTTP requests
- URL construction
- Request parameters
- HTTP error handling
- Response parsing

The rest of the application should operate on application-level data rather than raw TMDB HTTP responses wherever practical. This allows TMDB to be replaced or mocked without rewriting business logic.

### VIII. Asynchronous Work

Operations that are slow, externally dependent, or potentially long-running MUST NOT block API requests. Background processing MUST use a task queue and worker architecture.

The API should:

```
Create Job → Enqueue Task → Return Job ID
```

The worker should:

```
Receive Task → Execute Service → Update Job State
```

Background tasks MUST delegate business logic to services rather than becoming a second location for business rules.

### IX. Idempotency

Operations that may be retried MUST be designed to be idempotent wherever practical. In particular:

- Movie imports MUST NOT create duplicate movies
- Trending synchronization MUST safely handle repeated execution
- Background tasks MUST tolerate retries
- Watchlist additions MUST NOT create duplicate entries

Database constraints SHOULD enforce important uniqueness guarantees rather than relying exclusively on application checks.

### X. Reliable Background Jobs

Background jobs MUST explicitly track their lifecycle. At minimum, jobs must transition through these states:

- `queued`
- `processing`
- `completed`
- `failed`

Jobs SHOULD record:

- Job ID
- Job type
- Progress
- Creation time
- Start time
- Completion time
- Error information

Transient external failures SHOULD be retried. Permanent failures MUST transition the job to `failed` and provide useful diagnostic information. A failed job MUST NOT leave the application in an ambiguous state.

### XI. Configuration and Secrets

Configuration MUST be supplied through environment variables or an equivalent configuration mechanism. Secrets MUST NOT be committed to source control. In particular, the following MUST be configurable independently of application code:

- `TMDB_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`

The TMDB API key MUST NEVER be exposed to the frontend.

### XII. Docker as the Development Environment

The complete application MUST be runnable using Docker Compose. The development environment MUST include separate services for:

- `frontend`
- `api`
- `worker`
- `scheduler`
- `postgres`
- `redis`

Services MUST communicate using Docker service names rather than relying on `localhost` for inter-container communication. A developer should be able to start the application with `docker compose up` where practical. The application should minimize differences between the development and production runtime environments.

### XIII. Database Migrations

Database schema evolution MUST use Alembic migrations. The project MUST NOT rely on `Base.metadata.create_all()` as the primary mechanism for managing schema changes. Every schema change that affects persisted data should have a corresponding migration. Migrations MUST be reviewable and reproducible.

### XIV. API Contracts

API request and response contracts MUST be explicitly represented using Pydantic schemas. Database models MUST NOT automatically become the public API contract. The application SHOULD maintain separate:

- Database Models ≠ API Schemas

This allows the persistence model and public API to evolve independently.

## Testing Standards

Business logic MUST be testable in isolation. Tests SHOULD:

- Exercise services without HTTP or framework dependencies
- Mock external API clients at the integration boundary
- Verify business rules independently of delivery mechanism

## Incremental Delivery

Features SHOULD be delivered incrementally. Each increment MUST:

- Maintain existing architectural boundaries
- Not break previously working functionality
- Be independently testable and deployable

## Governance

This constitution governs all code within the Movie Discovery project. All pull requests and code reviews MUST verify compliance with the principles above.

Amendments to this constitution MUST:

1. Be documented with rationale
2. Increment the version number according to semantic versioning (MAJOR for principle removals/redefinitions, MINOR for new principles/material expansions, PATCH for clarifications)
3. Update the `Last Amended` date

Compliance reviews SHOULD occur during code review. Architectural boundary violations MUST be justified in writing before merging.

**Version**: 1.1.0 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-09-02
