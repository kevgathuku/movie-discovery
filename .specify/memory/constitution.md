<!--
Sync Impact Report
Version change: N/A → 1.0.0 (initial ratification)
Added sections: All (initial constitution)
Removed sections: None
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

## Testing Standards

Business logic MUST be testable in isolation. Tests SHOULD:

- Exercise services without HTTP or framework dependencies
- Mock external API clients at the integration boundary
- Verify business rules independently of delivery mechanism

## Containerized Development

The development environment MUST be containerized to ensure consistency across machines and contributors. The container setup SHOULD:

- Match production runtime dependencies
- Support hot-reload for development
- Be documented and reproducible

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

**Version**: 1.0.0 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-09-02
