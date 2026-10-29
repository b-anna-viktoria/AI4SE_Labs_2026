# EventTicket architecture discussion notes

## Requirements baseline

- Public event discovery and browsing.
- Registration, login, logout, personal pages, and password recovery.
- Users can favourite categories and receive email notifications about matching events.
- Users can book pre-sales and view bookings.
- Users can buy tickets online, pay, receive ticket codes, and view purchased tickets.
- Managers can create events and view their proposed events.
- Admins can add managers.

## Architecture options introduced

1. **Modular monolith** — one deployable application with well-separated business modules and a shared relational database. It emphasizes straightforward delivery and cross-feature transactions.
2. **Microservices** — independently deployed services for domains such as identity, events, reservations, payments, ticketing, and notifications. It emphasizes service-level autonomy and scaling, with distributed-system overhead.
3. **Serverless, event-driven architecture** — managed functions and services react to HTTP requests and asynchronous events, with managed storage, queues, and external integrations. It minimizes server management but requires deliberate workflow and retry handling.

### Initial comparison

The modular monolith keeps complexity mostly within one application and supports simple transactional boundaries. Microservices distribute ownership, deployment, and scaling but require network contracts and eventual consistency. Serverless shifts infrastructure operations to managed providers while making asynchronous workflow state, retries, and debugging central concerns. All options can satisfy the stated user stories.

## Architecture 1: modular monolith — detailed discussion

### Component structure

```text
Browser / Web UI
       |
       | HTTPS
       v
Web application
  +-- Public event browsing
  +-- Identity, sessions, password recovery, roles
  +-- User profile and favourite categories
  +-- Event management (manager/admin)
  +-- Pre-sale reservations
  +-- Checkout and payment coordination
  +-- Ticket issuance and ticket lookup
  +-- Notification orchestration
       |
       +------ Relational database
       |         users, roles, events, categories,
       |         reservations, payments, tickets,
       |         favourites, notification preferences
       |
       +------ Background worker / job queue
       |         email delivery, expiry jobs, retries
       |
       +------ Payment provider (API + signed webhooks)
       |
       +------ Email provider
```

The modules live in one codebase and are deployed together. They should expose explicit internal interfaces and avoid reaching into each other's tables or implementation details. The relational database is shared, but ownership of tables and transaction boundaries should remain clear. A worker can initially run as a separate process from the same application code, using a database-backed queue or a small queue service.

### Data flows

#### Browse and publish events

1. A visitor requests the event list or event details.
2. The event-browsing module queries published events, with pagination and category/date filters.
3. A manager submits an event form; the application authenticates the account and checks the manager role and ownership rules.
4. The event-management module validates and stores the event, initially in a draft/pending or published state according to the product's publication policy.

#### Register, sign in, and recover an account

1. The identity module validates registration data, stores a password hash (never the raw password), and establishes a session after successful login.
2. Requests to protected functions resolve the session and check the relevant user/manager/admin permissions.
3. Password recovery issues a short-lived, single-use token and sends a reset link via the email provider; the token is verified and invalidated when the password is changed.

#### Reserve, pay, and issue a ticket

1. The user starts a pre-sale reservation or checkout for a particular event/ticket type.
2. In a database transaction, the application checks availability and creates a reservation with an expiry, preventing concurrent requests from overselling inventory.
3. For paid checkout, the payment-coordination module creates a payment attempt with the provider using an idempotency key. The user is redirected to or otherwise completes the provider's payment flow.
4. A verified provider webhook (rather than only the browser redirect) confirms the final payment result. The application records it idempotently and transitions the reservation/payment state.
5. On confirmed payment, the application creates the ticket and its unpredictable ticket code exactly once, then exposes it in the user's account and sends a confirmation email.
6. If payment fails or the reservation expires, the reservation is released and no usable ticket is issued.

Exact state names, pre-sale payment rules, and whether pre-sale consumes limited inventory are policy decisions not specified by the user stories.

#### Category notifications

1. A user saves favourite categories or notification preferences.
2. When a matching event is published, the application creates a notification job.
3. A background worker sends the email and records success or a retryable failure, avoiding slow email delivery in the event-publication request.

### How this architecture addresses the requirements

- Public browsing and event management are supported by separate modules in the same web application.
- Identity and role checks can be shared consistently across user, manager, and admin pages/actions.
- Profile, favourites, pre-sale bookings, and tickets are direct account-scoped queries.
- Reservation, payment-state, and ticket-issuance changes can use database transactions and uniqueness constraints within one database.
- Payment and email remain external integrations, with webhook handling and background work isolated behind module interfaces.
- The architecture does not require independent service deployment or complex infrastructure before traffic and team needs justify it.

### Advantages

- Lowest operational and deployment complexity of the three options.
- Easier local development, debugging, and end-to-end testing.
- Database transactions and constraints simplify correctness for bookings and ticket issuance.
- One codebase supports rapid iteration while feature boundaries can still be enforced.
- Shared authentication, authorization, validation, and observability are easier to apply consistently.
- Modules can later be extracted if scaling, ownership, or deployment needs make that worthwhile.

### Disadvantages

- The whole application is generally deployed and scaled as one unit.
- Poor module boundaries can lead to a tightly coupled "big ball of mud" and shared-table contention.
- A slow or resource-heavy feature can affect unrelated requests unless workload separation and limits are used.
- Changes to shared code/schema require coordination and can increase regression risk.
- Independent teams cannot release their domains as freely as with well-separated services.

### Bottlenecks and pressure points

- **Inventory contention:** popular events can cause many concurrent attempts to reserve the last seats. Database row locks, conditional updates, transaction duration, and clear expiry handling matter.
- **Database hot spots:** event listing, ticket availability, and booking writes all rely on the same database. Indexes, pagination, query plans, connection pooling, and read/write load need attention as traffic grows.
- **Payment-provider latency and outages:** checkout must not hold database locks while waiting on remote calls. Webhooks can be delayed, duplicated, or delivered out of order.
- **Synchronous email:** sending email inside a web request increases latency and couples availability to the provider; use a durable job/outbox pattern and bounded retries.
- **Monolithic resource contention:** reports, bulk notifications, or other CPU/IO-heavy jobs can compete with interactive checkout unless run in a separate worker process with controlled concurrency.
- **Ticket-code lookup and abuse:** code generation must avoid collisions and codes must not be guessable; lookup endpoints should be rate-limited and avoid leaking personal data.

### Hardest implementation details

- Designing a reservation/payment/ticket state machine that handles retries, cancellation, expiry, provider webhooks, and duplicate/out-of-order notifications without double charging or issuing duplicate tickets.
- Preventing overselling under concurrent bookings while keeping transactions short. Enforce invariants in the database, not only in application-level checks.
- Making external side effects reliable: persist the intent to send notifications or issue follow-up work transactionally (for example with an outbox), then process with idempotent workers.
- Securing role- and ownership-sensitive actions: an authenticated user must not be able to edit another manager's event or see another user's bookings/tickets.
- Handling password-reset tokens, session invalidation, and account lifecycle securely.
- Defining cancellation/refund, reservation timeout, and pre-sale policy; the provided stories do not fully specify these business rules.
- Keeping module boundaries meaningful while sharing one database and codebase.

### Recommended testing strategy

1. **Unit tests:** business rules and state transitions for roles, event publication, reservation expiry, payment outcomes, ticket issuance, and notification matching. Use deterministic clocks and generated IDs where practical.
2. **Database integration tests:** migrations, constraints, transaction rollback, ownership-scoped queries, and concurrent reservation attempts against the actual database engine used in production. Verify that inventory cannot go below zero.
3. **Module/API tests:** exercise request validation, authorization, response shapes, and module interfaces with external services stubbed at their boundaries.
4. **Payment contract tests:** validate request/response and webhook signature handling against provider test fixtures or a sandbox; cover duplicate, delayed, invalid-signature, and out-of-order webhooks.
5. **Worker tests:** verify retry/backoff, idempotency, dead-letter/error reporting, and that failed email delivery does not lose the event or payment result.
6. **End-to-end tests:** cover registration/login, manager event creation, user discovery, reservation, successful and failed payment, ticket visibility, and password recovery. Keep the critical purchase flow in a small, reliable smoke suite.
7. **Load/concurrency tests:** focus on event listing and simultaneous reservation/checkout for scarce inventory; measure database saturation, response latency, and error rates.
8. **Security tests:** authorization matrix across client/user/manager/admin, password-reset misuse, CSRF/session protections, input validation, and ticket-code access controls.

### Failure impact and isolation

Sharing a codebase does **not automatically** mean that every defect takes down every feature. The impact depends on where the error occurs and how the application is run:

- A defect in one module's business logic may be limited to that operation if errors are handled at the request/job boundary and module interfaces are respected.
- An unhandled exception in a web request will usually fail that request, but the web server can continue serving other requests. A process-level crash, memory exhaustion, or deadlock can affect all features hosted in that process.
- Shared infrastructure creates broader failure modes: database unavailability or overload affects most data-backed features, and a bad schema migration can break multiple modules.
- Modules deployed together share a release and rollback boundary. A faulty change can therefore affect the whole application even if the change is in one module.
- A slow external dependency can consume threads or connections if calls have no timeouts or isolation. An email outage should not block event publishing or checkout.
- Resource-heavy background jobs can compete with interactive requests if they run in the same process or share unconstrained resources.

Mitigations include keeping module interfaces and ownership clear; catching and reporting errors at appropriate request/job boundaries without masking them; using database transactions and constraints for invariants; applying timeouts, bounded retries, and circuit-breaking behavior to external calls; and processing email/expiry work in a separate worker process with concurrency limits. Separate web and worker processes reduce resource and process-failure coupling while retaining a shared codebase. Health checks, structured logs, metrics, and alerting help detect when a localized fault is becoming systemic.

This architecture still has a larger shared deployment and infrastructure blast radius than independently deployed microservices. The modular monolith trades some fault isolation for simpler transactions and operations; it can reduce—but not eliminate—cross-feature impact through strong boundaries and process separation.

## Architecture 2: microservices — detailed discussion

### Component structure

```text
Browser / Web UI
       |
       | HTTPS
       v
API Gateway / Backend-for-Frontend
  - routing, request limits, response composition
  - validates access tokens (or delegates to identity)
       |
       +------------------+--------------------+--------------------+
       |                  |                    |                    |
       v                  v                    v                    v
 Identity service    Event service      Reservation service   Account / ticket
 - registration      - event catalog    - holds and expiry     query endpoints
 - login / roles     - manager events   - inventory ownership  (may be APIs on
 - password reset    - categories                                  domain services)
       |                  |                    |                    |
   Identity DB         Event DB          Reservation DB        Ticket service
                                               |                - ticket codes
                                               |                - ticket lookup
       +----------------------+----------------+--------------------+
                              |
                         Message broker
                  (domain events; asynchronous work)
                    /              |               \
                   v               v                v
           Payment service   Ticket service   Notification service
           - provider API    - issue/revoke    - category email
           - webhook handler - ticket store    - delivery status
                 |                                 |
          Payment provider                    Email provider
```

Services are independently deployable units organized around business capabilities, not merely technical layers. Each service owns its data and exposes it through APIs or events; other services should not query or write its database directly. In a fuller design, the ticket service owns its own database as well, and the diagram's shared ticket/account area represents APIs and projections rather than a shared datastore. The gateway is an entry point, not a place for domain rules. A message broker supports asynchronous events, while synchronous APIs are reserved for interactions that need an immediate answer.

The split shown is one possible design, not a requirement to create one service per noun. For a small team or early product, fewer coarser-grained services may be more practical.

### Data flows

#### Browse and publish events

1. The browser requests event listings through the gateway, which routes to the event service.
2. The event service reads its own event store and returns published event data, with paging and filters.
3. A manager's authenticated create/update request is authorized by the event service using identity claims and event ownership rules.
4. On publication, the event service commits the event and an `EventPublished` message reliably (typically with a transactional outbox), then the notification service consumes it and finds users with matching category preferences.

#### Registration and identity

1. Registration, login, and password recovery are handled by the identity service, which owns credentials, sessions/tokens, roles, and reset-token state.
2. The gateway validates or forwards identity tokens; each service still enforces authorization for its own operations, including resource ownership.
3. User profile and notification preferences belong to an explicitly chosen owner (for example, an account/preferences service); they should not become an unowned shared database.

#### Reserve, pay, and issue a ticket

1. The user asks the reservation service to reserve a ticket type. That service atomically checks and reserves inventory in its own database, returning a reservation identifier and expiry.
2. The payment service creates a payment attempt with the external provider, using an idempotency key and associating it with the reservation. Remote provider calls should not occur while a database transaction or inventory lock is held.
3. The provider sends a signed webhook to the payment service. The service validates it, records the provider event idempotently, and publishes a payment outcome.
4. A workflow coordinator (which may be implemented inside the reservation or payment service at first) reacts to the outcome. On success, it marks the reservation paid/confirmed and requests ticket issuance; on failure or timeout, it releases the hold according to the agreed policy.
5. The ticket service consumes the issuance request, creates a unique, unpredictable ticket code idempotently, and publishes `TicketIssued`.
6. Account pages obtain bookings and tickets through their owning services, or through a read-only projection updated from domain events. The notification service sends confirmation email asynchronously.

There is no single ACID transaction spanning these services. The purchase is a **saga**: a sequence of local transactions with explicit states, retries, and compensating actions (such as releasing an expired hold or initiating a refund if a late payment succeeds after inventory has been released). The exact policy must be defined before implementation.

#### Category notifications

1. The event service emits publication events; the preferences owner supplies or exposes category subscriptions.
2. The notification service deduplicates and schedules matching email work.
3. It calls the email provider, recording delivery state and retrying transient failures without blocking event publication or checkout.

### How this architecture addresses the requirements

- Separate services provide event discovery/management, identity and roles, user reservations, payments, ticket issuance, and category notifications.
- Manager/admin permissions can be enforced at the service owning each operation, rather than relying solely on the gateway or UI.
- Reservation service ownership of inventory allows booking rules to be scaled and changed independently.
- Payment and ticket services can handle provider-specific concerns and protect ticket issuance with idempotent event handling.
- Async events allow email and other follow-up tasks to proceed independently of interactive requests.
- Read APIs or projections can assemble personal-page views across bookings and tickets, but must tolerate eventual consistency.

### Advantages

- Services can be deployed and scaled independently where demand differs (for example, event browsing vs. checkout).
- Failures can be more isolated when services have bounded resources, timeouts, and carefully designed dependencies.
- Clear ownership can support separate teams and domain-specific evolution.
- A service can use a storage technology suited to its needs, if justified.
- Asynchronous events decouple notifications and other follow-up work from the request path.

### Disadvantages

- Considerably more infrastructure and operational work: service discovery/routing, deployment pipelines, secrets, metrics, tracing, broker operations, and incident response.
- A user's purchase spans multiple local transactions and may be temporarily inconsistent; there is no simple cross-service rollback.
- Network calls add latency and introduce timeouts, partial failures, retries, and versioning concerns.
- Data duplication and projections complicate personal pages, reporting, and deletion/correction workflows.
- Local development and automated tests require coordinating service instances, contracts, broker behavior, and test data.
- Splitting too early can create many small services without enough team or traffic to justify their cost.

### Team ownership and data-leak risks

Microservices can be developed and operated by separate teams, with each team owning a service and its data. They are then integrated through agreed APIs and event contracts, authentication/authorization rules, and deployment compatibility expectations. "Build separately, then connect" is possible, but it is not plug-and-play: teams need shared standards for service discovery, identity, error handling, versioning, observability, and ownership boundaries.

Data leaks are a **risk if the boundaries and controls are implemented poorly**, not an inevitable consequence of microservices. More service APIs, event streams, data copies, and credentials create additional places where sensitive information could be exposed. Examples include:

- an endpoint checking that a caller is logged in but not checking that the requested booking or ticket belongs to that user;
- a service trusting user IDs or roles supplied by the browser or an upstream service without validating their source and scope;
- publishing personal or payment-related fields in broad broker events when consumers only need a minimal identifier and status;
- overly permissive service credentials, network access, logs, or read projections exposing data to components that do not need it;
- stale or improperly filtered account-page projections showing another user's data.

Reduce these risks by enforcing authentication and resource-level authorization in every service; using least-privilege service identities and database/broker permissions; validating signed tokens and webhook signatures; encrypting traffic and protecting secrets; publishing only the minimum necessary event fields; filtering projections by the authenticated user; avoiding sensitive data in logs; and auditing access to sensitive operations. Security tests should include cross-user and cross-role access attempts at each service boundary.

### Bottlenecks and pressure points

- **Reservation/inventory service:** popular events still produce contention on the service that owns inventory. Microservices do not remove the need for atomic capacity control.
- **Broker throughput and consumer lag:** a backlog can delay ticket issuance or email. Monitor lag, processing time, retries, and dead-letter queues.
- **Synchronous dependency chains:** gateway → identity → reservation → payment calls can accumulate latency and availability dependencies. Keep critical request paths short and use explicit deadlines.
- **Hot services and shared infrastructure:** a single reservation database, broker partition, gateway, or identity provider can still become a system-wide bottleneck.
- **Cross-service account views:** querying many services on every profile page increases tail latency and failure exposure; a projection improves reads but can be stale.
- **Payment webhook processing:** duplicate deliveries, delayed confirmation, and provider outages can create retries and state buildup; event handling must be idempotent and observable.
- **Chatty service boundaries:** fine-grained synchronous calls can erase scaling benefits and make even simple page loads slow.

### Hardest implementation details

- Defining service boundaries, data ownership, and stable API/event contracts without splitting too finely or creating hidden shared-database coupling.
- Implementing the purchase saga: state transitions, idempotency keys, event deduplication, timeout races, late payment success, inventory release, refunds, and recovery after partial failure.
- Achieving reliable event publication and consumption, commonly using an outbox/inbox approach, at-least-once delivery, idempotent consumers, and replay-safe handlers.
- Maintaining authorization across services: token validation, role changes, tenant/resource ownership, and avoiding trust in client-supplied identity data.
- Operating schema and contract changes safely while producers and consumers deploy at different times.
- Providing end-to-end observability across a user action that traverses services and asynchronous events.
- Handling data deletion, correction, and account closure across services and derived projections.

### Recommended testing strategy

1. **Service unit tests:** validate each service's business rules and state transitions independently, especially inventory, payment, and ticket lifecycle logic.
2. **Service database integration tests:** test local transactions, constraints, migrations, and concurrent inventory reservation against each service's production database engine.
3. **API and event contract tests:** verify request/response and event schemas between each producer and consumer; use consumer-driven contract checks where useful.
4. **Provider integration tests:** test payment requests, webhook signatures, idempotency, and email behavior using provider sandbox/test fixtures.
5. **Messaging tests:** cover duplicate, delayed, reordered, replayed, and malformed events; verify outbox delivery, consumer idempotency, retry policies, and dead-letter handling.
6. **Saga/workflow tests:** exercise success, payment failure, expiry racing with payment, late payment, ticket-issuance retry, and compensation/refund paths using controllable dependencies.
7. **End-to-end tests:** run a small number of full user journeys across deployed test services, including manager event publication, user booking/payment, and ticket visibility.
8. **Resilience and load tests:** test service timeouts, broker/database outages, consumer lag recovery, and high contention on the last available tickets. Measure end-to-end latency and error rates.
9. **Security tests:** validate authorization at every service boundary, token expiry/revocation behavior, webhook verification, and protection against insecure direct object references.

### Comparison with Architecture 1 (modular monolith)

- **Consistency:** the monolith can use one database transaction for booking-related state; microservices require a saga and eventual consistency.
- **Isolation and scaling:** microservices permit independent deployment/scaling and can narrow some process-level failures, but shared infrastructure and service dependencies remain failure points.
- **Development and operations:** the monolith is simpler to develop, test, deploy, and debug; microservices add contracts, distributed tracing, broker operations, and more deployment coordination.
- **Team/product fit:** microservices become more compelling when independent teams, uneven scaling, or operational ownership justify the cost. For the stated stories alone, a modular monolith is likely the simpler initial choice; good module boundaries can preserve a path to extraction later.

## Architecture 3: serverless, event-driven — detailed discussion

### Component structure

```text
Browser / Web UI
       |
       | HTTPS
       v
Managed web hosting / CDN
       |
       v
API Gateway + managed identity integration
       |
       +---- Request functions
       |       - event browsing and manager operations
       |       - profile, favourites, booking queries
       |       - reservation and checkout commands
       |       - password recovery endpoints
       |
       +---- Managed relational database
       |       or other managed datastore with conditional writes
       |
       +---- Event bus / queue <----- Payment webhook function
       |       |                           ^
       |       |                           |
       |       +--> Workflow orchestrator  Payment provider
       |       |     - purchase saga
       |       |     - retries / timeouts
       |       |
       |       +--> Ticket issuance function
       |       +--> Notification function ---> Email provider
       |       +--> Scheduled expiry function / timer
       |
       +---- Logs, metrics, tracing, secrets and key management
```

In this option, the platform provider runs and scales the functions, gateway, queue/event bus, workflow engine, timers, and usually the database. Functions are typically short-lived and should not rely on local memory or disk for durable state. Components can still be grouped by business responsibility; serverless does not require one function for every tiny operation. A managed relational database remains a reasonable choice for transactional inventory, if its connection and scaling model suits the platform.

### Data flows

#### Browse and publish events

1. The browser loads the web UI from managed hosting/CDN and calls the API gateway.
2. The gateway invokes an event-query function. It validates inputs and reads published events from the managed datastore, using pagination and appropriate indexes.
3. A manager's event create/update request invokes a function that checks identity, role, and event ownership before writing.
4. On publication, durable event work is placed on an event bus or queue (for example via a transactional outbox or datastore change stream). A notification function processes the publication asynchronously and identifies matching category subscribers.

#### Registration and identity

1. Registration, login, and password recovery use a managed identity provider or dedicated functions integrated with one.
2. The gateway can verify identity tokens, but each function still checks authorization and resource ownership before returning or changing data.
3. Password recovery uses short-lived, single-use reset tokens and asynchronous email delivery; credentials and tokens are never placed in logs or broad event payloads.

#### Reserve, pay, and issue a ticket

1. A reservation function performs an atomic conditional database operation or short transaction to hold capacity and create a reservation expiry. It must not depend on a read-then-write sequence without concurrency protection.
2. A workflow orchestrator records the purchase steps and starts the payment provider interaction with an idempotency key.
3. A payment webhook reaches a dedicated endpoint/function, which verifies the provider signature and durably records the provider event before acknowledging it.
4. The workflow resumes from the payment outcome. On success it confirms the reservation and invokes ticket issuance; on failure or expiry it releases the hold according to policy.
5. Ticket issuance creates a unique, unpredictable code idempotently and records the ticket. A notification function sends the confirmation separately.

The workflow is still a saga: platform-managed orchestration does not create one ACID transaction across the database and payment provider. Duplicate events, timeouts, late payment results, retries, and compensation (such as refunding a late successful charge) must be explicitly handled.

#### Category notifications and expiry

1. Event publication triggers notification work through a queue/event bus; the function determines matching users and requests email delivery.
2. Scheduled functions or managed timers release expired reservations and update state.
3. Queue retries and a dead-letter destination preserve failed work for diagnosis, but operational monitoring and safe replay are still required.

### How this architecture addresses the requirements

- HTTP functions cover public event discovery, account features, manager event operations, and admin manager creation.
- A managed identity provider or identity functions handle registration, login, logout, roles, and password recovery.
- Database-backed user preferences support favourite categories; publication events trigger email notifications.
- Reservation functions enforce inventory rules with atomic database operations; workflow orchestration coordinates payment and ticket issuance.
- Ticket data remains durable in a managed datastore and is available through authenticated account queries.
- Managed timers, queues, and email integrations handle reservation expiry and asynchronous confirmations without keeping request handlers waiting.

### Advantages

- Little or no server fleet management; platform services provide execution, routing, queues, and often identity and monitoring.
- Functions can scale automatically with request or event volume, and unused components may have low idle cost depending on provider pricing.
- Asynchronous notifications, expiry, and payment workflows naturally fit event triggers and managed orchestration.
- Smaller handlers can be deployed independently, and managed services provide useful durability and retry primitives.

### Infrastructure ownership, availability, and data responsibility

The team usually does **not** build or operate the cloud provider's underlying servers, gateways, queue fleet, or database hardware. The team still designs the system and configures/deploys its cloud resources, function code, schemas, permissions, networking, monitoring, backups, and recovery plans—preferably with infrastructure-as-code. Managed serverless reduces infrastructure operations; it does not remove architecture, configuration, or operational responsibility.

A managed cloud database can reduce the team's hardware maintenance burden and may offer backups, replication, and multi-zone failover options. That can improve availability compared with a single self-managed database instance, **if** the relevant options are selected, configured, tested, and paid for. It does not guarantee availability: provider or regional outages, misconfiguration, quota exhaustion, bad migrations, application-level overload, and network failures can still make it unavailable. Check the provider's service-level agreement and recovery objectives, and design backups, restore tests, monitoring, and (where justified) regional recovery around the product's needs. Cloud hosting by itself does not make an outage less likely.

Using a cloud provider or other external providers (such as payment and email providers) means data is processed by third parties. This warrants careful attention, but the security responsibility is shared: the provider secures parts of its managed platform, while the application team remains responsible for what data it collects, how it configures access, and what it sends or stores. Teams should classify personal/payment-related data; minimize what they collect and transmit; review provider security, privacy, retention, residency, and contractual terms; restrict identities and permissions; encrypt data in transit and at rest; manage keys and secrets; avoid sensitive logs; audit access; and define deletion, backup retention, and incident-response procedures. Applicable privacy and payment obligations depend on the jurisdictions, providers, and exact data flows and should be confirmed with the appropriate organizational/legal/security experts.

### Disadvantages

- Strong dependency on provider-specific services and semantics can create vendor lock-in and complicate migration.
- Cost is less predictable under high or bursty traffic, repeated retries, chatty function calls, or inefficient data access.
- Function execution limits, cold starts, concurrency quotas, and database connection limits constrain design choices.
- Workflows are distributed and asynchronous; observing and debugging them across logs, queues, and provider consoles can be difficult.
- Local development and realistic testing require emulating or provisioning managed services.
- Serverless is not automatically cheaper, more reliable, or more secure; configuration and application-level correctness still matter.

### Bottlenecks and pressure points

- **Inventory database:** bursts of concurrent reservations still contend on the same event/ticket-type records. Atomic updates, correct indexes, and database capacity remain essential.
- **Database connections:** many concurrently started functions can exhaust relational database connections. Use provider-supported pooling/proxies, concurrency limits, or a datastore designed for the access pattern.
- **Concurrency quotas and throttling:** sudden bursts or configured account limits may cause requests or consumers to be throttled; retries can amplify the burst if not bounded and jittered.
- **Cold starts and execution limits:** infrequent functions may add latency, while long work may exceed maximum execution duration and need decomposition into queued steps.
- **Queue backlogs and retries:** notification or ticket jobs may lag; poison messages and retry storms can increase costs or block partitions if not isolated.
- **Workflow/provider limits:** long-running state machines, payload size, transition count, and external API limits can constrain purchase orchestration.
- **Cost amplification:** inefficient polling, excessive small function invocations, repeated state transitions, and failed retries can produce unexpectedly high bills.
- **Observability fragmentation:** one user action spans gateway, functions, database, workflow, and queue; missing correlation IDs make diagnosis slow.

### Hardest implementation details

- Modeling reservation, payment, expiry, refund, and ticket issuance as a durable workflow that safely resumes after every timeout or retry.
- Guaranteeing idempotency at each side-effect boundary: API retries, payment webhooks, queue delivery, and ticket creation.
- Making event publication reliable with the database update (outbox/change stream) so a saved event or payment result cannot silently lose its follow-up work.
- Enforcing inventory capacity atomically while operating within the chosen managed datastore's transaction and conditional-write limits.
- Choosing sensible function boundaries and avoiding both a monolithic handler and excessive function-to-function chatter.
- Managing database connection bursts, secrets, permissions, environment configuration, and infrastructure-as-code across environments.
- Building correlation, tracing, alerting, dead-letter inspection, and safe replay into operational workflows.
- Avoiding sensitive data leakage through logs, event payloads, and overly broad function roles.

### Recommended testing strategy

1. **Function unit tests:** validate domain rules, input handling, authorization decisions, state transitions, and idempotency using deterministic time and identifiers.
2. **Data-layer integration tests:** test production-engine transactions/conditional updates, constraints, migrations, and concurrent reservation attempts to prove no overselling.
3. **Event and workflow tests:** verify event schemas, workflow success/failure paths, timeout and retry behavior, duplicate webhook/message handling, reservation expiry races, late payment, compensation, and replay.
4. **Provider contract/sandbox tests:** test gateway authentication, payment requests and webhook signatures, email requests, and managed identity behavior using provider sandbox accounts or fixtures.
5. **Local cloud integration tests:** run handlers against local emulators where reliable, supplemented by an isolated deployed test environment because emulators may not reproduce provider limits and semantics.
6. **End-to-end tests:** exercise registration, manager event publication, discovery, reservation, payment, ticket visibility, notifications, and password recovery through the deployed gateway.
7. **Load and quota tests:** test traffic bursts, last-ticket contention, function concurrency, database connections, queue lag, throttling, and retry amplification; inspect latency and cost.
8. **Operational/security tests:** verify dead-letter handling and replay, alarms, trace correlation, least-privilege function roles, authorization, secret handling, and absence of sensitive data in logs.

### Comparison with Architectures 1 and 2

- **Versus the modular monolith:** serverless removes much server management and scales individual handlers more elastically, but replaces in-process calls and simple local operation with provider configuration, distributed workflows, and managed-service limits. The monolith keeps the easiest transactional model for the purchase flow.
- **Versus microservices:** both can have independently deployable components, API/event contracts, and eventual consistency. Serverless delegates more runtime and infrastructure management to a provider and often uses event-triggered functions/workflow services; microservices commonly run longer-lived service processes and give teams more control over runtime and deployment environments.
- **Common constraint:** neither serverless nor microservices removes inventory contention or payment-provider edge cases. Both require idempotency, durable workflow state, observability, and careful data authorization.
- **Fit:** serverless is attractive for variable traffic and a small team wanting managed infrastructure, if provider limits and lock-in are acceptable. A modular monolith is simpler when traffic and team structure are modest; microservices suit independently owned domains where operational maturity supports them.

## Conversation updates

- First explored Architecture 1 (modular monolith) in detail.
- Clarified that shared codebase does not mean every error affects every feature: request-level failures may stay local, while process crashes, shared database problems, resource contention, or faulty shared releases can have wider impact. Noted mitigations and the trade-off against independent services.
- Explored Architecture 2 (microservices) in detail, including service-owned data, API gateway, event broker, reservation/payment/ticket saga, bottlenecks, implementation challenges, and testing strategy.
- Compared microservices with Architecture 1: greater independent scaling and deployment, but substantially more distributed consistency, operational, and testing complexity.
- Clarified that microservices can be owned and implemented by separate teams, provided they integrate through agreed contracts and shared operational/security standards. Discussed data leaks as a preventable risk from weak authorization, excessive event/data sharing, broad credentials, or unsafe projections, and recorded mitigations.
- Explored Architecture 3 (serverless, event-driven) in detail: managed gateway/identity, functions, database, event bus/queues, workflow orchestration, payment and email providers, plus workflow data flows, bottlenecks, implementation challenges, and testing strategy.
- Compared serverless with both earlier options: it reduces server operations but adds provider coupling and managed-service constraints; its purchase flow still needs saga-style consistency and idempotency.
- Clarified that the team configures and operates the application-level cloud resources rather than building the provider's infrastructure. Managed database features can improve availability when deliberately configured, but do not guarantee uptime. Recorded shared-responsibility and third-party data protection considerations.
