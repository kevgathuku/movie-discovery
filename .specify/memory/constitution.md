<!--
Sync Impact Report
Version change: 1.1.0 → 1.2.0 (MINOR: new principles and sections added)
Modified principles: None renamed
Added principles:
  XV. Testability
  XVI. Dependency Injection
  XVII. Simplicity Over Abstraction
  XVIII. Single Application Boundary
  XIX. Observability
  XX. Error Handling
  XXI. Data Ownership
  XXII. Incremental Development
  XXIII. Feature Specifications Must Define Boundaries
  XXIV. Security Baseline
  XXV. Performance Principles
Added sections: Definition of Done, Guiding Principle
Removed sections: Testing Standards (superseded by Principle XV),
  Incremental Delivery (superseded by Principle XXII)
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

### XV. Testability

Business logic MUST be testable independently of HTTP. Services SHOULD be testable without starting FastAPI. External API clients MUST be mockable. Tests MUST NOT depend on the availability of the real TMDB service.

The test suite should contain separate coverage for:

- Services
- Repositories
- API endpoints
- Background tasks

Critical business rules MUST have automated tests.

### XVI. Dependency Injection

Dependencies such as database sessions, services, repositories, external clients, and configuration SHOULD be injected rather than instantiated throughout application code. FastAPI's dependency injection system should be used at the application boundary.

This enables:

- Easier testing
- Mocking
- Explicit dependencies
- Replacement implementations

### XVII. Simplicity Over Abstraction

The project MUST avoid unnecessary abstraction. Architectural patterns should be introduced when they solve an actual problem. Do not introduce:

- Generic repositories without a demonstrated need
- Excessive factory patterns
- Deep inheritance hierarchies
- Framework-specific abstractions without clear value
- Premature microservices

Prefer straightforward Python and explicit dependencies. The architecture should be sophisticated enough to demonstrate good engineering practices without becoming an architecture exercise in itself.

### XVIII. Single Application Boundary

The initial project MUST remain a modular monolith. The backend should be deployed as one logical application consisting of:

- API
- Worker
- Scheduler

These may run as separate processes or containers but should share the same application domain and codebase. The project MUST NOT introduce microservices unless a concrete requirement demonstrates the need.

### XIX. Observability

Important operations MUST produce useful structured logs. Logs SHOULD contain contextual identifiers where available:

- `request_id`
- `job_id`
- `tmdb_id`
- `task_name`

Errors MUST provide enough context to diagnose failures without exposing secrets. Sensitive credentials MUST NEVER appear in logs.

### XX. Error Handling

Errors MUST be handled at the appropriate architectural boundary. Expected domain errors should use explicit domain exceptions. For example:

- `MovieNotFoundError`
- `MovieAlreadyExistsError`
- `JobNotFoundError`

The API layer maps these to appropriate HTTP responses. External API errors should be translated into application-level errors where appropriate. Unexpected errors MUST NOT expose internal implementation details to API clients.

### XXI. Data Ownership

PostgreSQL is the source of truth for data owned by Movie Explorer. TMDB is the source of truth for externally sourced movie metadata. The application MAY cache or normalize TMDB data locally, but MUST distinguish between:

- External movie identity: `tmdb_id`
- Internal movie identity: `id`

The internal database ID MUST NOT be assumed to correspond to a TMDB ID.

### XXII. Incremental Development

Features MUST be implemented vertically where practical. Each feature should ideally provide a complete path through:

```
Frontend → API → Service → Repository / External Client → Database / External API
```

Avoid building large layers of unused infrastructure before implementing functionality that requires them. Each increment should leave the application in a runnable state.

### XXIII. Feature Specifications Must Define Boundaries

Every future feature specification should explicitly identify:

- User-visible behavior
- API changes
- Domain/business rules
- Database changes
- Background processing requirements
- External API requirements
- Frontend changes
- Testing requirements

A feature should not silently introduce architectural responsibilities into an unrelated layer.

### XXIV. Security Baseline

The application MUST:

- Keep secrets server-side
- Validate all external and user-provided input
- Avoid SQL injection through parameterized ORM/database operations
- Avoid exposing internal errors to clients
- Avoid logging secrets
- Validate external API responses before persisting important data

Authentication is intentionally deferred from the MVP but the architecture SHOULD allow it to be added later.

### XXV. Performance Principles

Performance optimizations should be based on actual bottlenecks. The application SHOULD:

- Avoid unnecessary TMDB requests
- Prefer local PostgreSQL reads for imported movies
- Use background jobs for expensive synchronization or import operations
- Paginate potentially large collections
- Consider caching only where useful

Premature optimization MUST NOT complicate the architecture.

## Definition of Done

A feature is considered complete only when:

- Its functional requirements are implemented
- Architectural boundaries are respected
- Required database migrations exist
- Relevant tests exist
- Error cases are handled
- Docker-based development continues to work
- API contracts are documented through FastAPI and Pydantic
- External integrations are mockable
- Background jobs are retry-safe where applicable
- The frontend handles loading, success, and failure states where applicable

## Guiding Principle

Build a boring, explicit, testable modular monolith with clear boundaries.

Prefer:

- Simple over clever
- Explicit over implicit
- Testable over tightly coupled
- Replaceable over prematurely distributed
- Observable over over-engineered

The architecture should make the correct path easy and the incorrect path obvious.

## Governance

This constitution governs all code within the Movie Discovery project. All pull requests and code reviews MUST verify compliance with the principles above.

Amendments to this constitution MUST:

1. Be documented with rationale
2. Increment the version number according to semantic versioning (MAJOR for principle removals/redefinitions, MINOR for new principles/material expansions, PATCH for clarifications)
3. Update the `Last Amended` date

Compliance reviews SHOULD occur during code review. Architectural boundary violations MUST be justified in writing before merging.

**Version**: 1.2.0 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-09-02
