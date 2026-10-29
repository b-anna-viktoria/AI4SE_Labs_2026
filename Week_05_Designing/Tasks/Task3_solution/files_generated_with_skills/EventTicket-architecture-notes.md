# EventTicket architecture discussion notes

> Scope: This discussion uses only `Tasks/data/EventTicket.txt` as the requirements source. Notes begin with this discussion; other text files were not consulted. The architectures are candidates, not stakeholder decisions.

## Requirements baseline

### Functional capabilities

- Public clients can visit the application and browse events.
- Clients can register, log in, log out, and regenerate a forgotten password.
- Users can view their personal data, save favourite categories, receive email notifications about related events, view pre-sale bookings, and view purchased tickets.
- Users can book a pre-sale, buy a ticket, pay online, and receive a ticket code.
- Managers can view their proposed events, publish/insert an event, and view their personal data.
- Admins can add managers and view their personal data.
- The requirements describe role-specific features for users, managers, and admins. They do not specify how roles are granted or whether a person can hold multiple roles.

### Business invariants and quality attributes

- **Inferred, important:** A ticket code should only be issued for a confirmed, successful payment; this follows from the story linking online payment to obtaining the code.
- **Inferred, important:** Ticket/pre-sale capacity should not be oversold if events have limited capacity. Capacity, seat selection, and the precise reservation policy are not specified.
- **Inferred:** Role checks and manager-to-event ownership must protect profile, event, and administration features.
- **Inferred:** Payment callbacks, email delivery, and password recovery require secure handling and safe retries.
- **Unknown:** Availability targets, expected traffic/peak sale rates, consistency expectations, deployment platform, team size/skills, budget, payment provider, email provider, and regulatory/data-residency obligations.
- **Unknown business policy:** Whether pre-sale is a temporary hold, a free booking, a paid early-access product, or another workflow; whether holds expire; and when payment is required.

## Architectural drivers and evaluation criteria

| Driver / criterion | Priority | Evidence or rationale |
|---|---|---|
| Correct reservation, payment, and ticket lifecycle | High (inferred) | Booking and payment lead to access to an event; ticket issuance must reflect the payment result. |
| Role and ownership enforcement | High (inferred) | User, manager, and admin stories expose different capabilities and data. |
| Functional coverage and evolvability | High | All three roles, event publication, profiles, favourites, notifications, bookings, purchases, and recovery need support. |
| Delivery and operational simplicity | Unknown / provisional | No scale, team, or operations constraints are stated; avoid paying complexity costs without evidence. |
| Burst scaling and failure isolation | Unknown | Event sales may be bursty, but no traffic or availability target is provided. |
| Data consistency across components | High for booking/payment | A paid ticket must not be duplicated or issued prematurely; the source implies this workflow but omits exact policy. |
| Provider dependence and reversibility | Unknown | Payment, email, cloud, and hosting providers are not specified. |

## Candidate architectures

| Candidate | Organizing idea | Main benefit | Main cost |
|---|---|---|---|
| A. Modular monolith | One web application, with explicit domain modules and one transactional relational database | Simplest way to build complete features and keep booking/payment state coherent | Shared deployment and runtime; module boundaries must be maintained by discipline |
| B. Domain microservices | Independently deployed services with explicit data ownership, APIs, and events | Independent scaling, release, and fault boundaries | Distributed state, event consistency, deployment, and operations complexity |
| C. Managed serverless / event-driven | API gateway and stateless functions, with managed workflows, queues, and data services | Elastic execution and less server administration; asynchronous work is natural | Cloud/provider coupling, retry/concurrency details, and database connection/throughput concerns |

## Architecture analysis

### A. Modular monolith with a relational database

- **Overview:** A single deployable web/API backend organized into domain modules. Modules call one another through internal interfaces; they are not separately deployed services.
- **Main components:** Web client; web/API entry point; identity/access and profiles; event catalog and manager event administration; favourites; booking/pre-sale; order/payment integration; ticket issuance; notification worker; relational database; payment and email providers.
- **Critical flow:** A user request is authenticated and authorized, then the booking module records a reservation/hold and capacity change in a database transaction. A payment adapter initiates payment. A verified provider callback updates the payment/order state idempotently; when policy says payment is confirmed, ticket issuance records the ticket and code. An outbox/worker sends email and other notifications without making provider availability part of the database transaction.
- **Requirement fit:** Modules cover the visitor, user, manager, and admin capabilities. A relational transaction can keep a capacity change and booking consistent. Role checks and manager ownership checks can be centralized in application policy helpers. Payment success and ticket issuance remain explicit states; email and favourite-category notifications can run asynchronously.
- **Advantages:**
  - Low initial deployment and operational complexity.
  - Strong transaction support for reservations, payments, and ticket records.
  - Easier end-to-end testing and local development than distributed candidates.
  - Domain boundaries can be evolved or extracted later if actual scaling or team needs justify it.
- **Scalability:** Scale the application and database vertically or by adding application instances behind a load balancer. This can handle growth while the database and capacity transaction remain sound, but a hot booking path cannot be scaled independently from other modules. Actual limits need load testing; no traffic estimate is available.
- **Maintenance implications:** One build, deployment, runtime, and primary data model simplify routine operations and upgrades. Teams must enforce module APIs and ownership boundaries to prevent a growing codebase and shared schema from turning into a tightly coupled monolith.
- **When another architecture is a better choice:** Choose microservices when independent team ownership, release cadence, fault isolation, or uneven scaling needs are demonstrated. Choose managed serverless when managed cloud services and elastic execution are strategic constraints and provider coupling is acceptable.
- **Disadvantages:**
  - One release and runtime for all modules; a faulty or resource-heavy module can affect the whole application.
  - Scaling one hot feature independently is limited; deployment coordination grows with the codebase.
  - A shared database can become coupled if modules access one another's tables directly.
- **Implementation challenges / painful details:**
  - Define module ownership and prohibit cross-module table writes.
  - Implement capacity changes with transactions/locking or conditional updates, plus uniqueness constraints to prevent duplicate reservations/tickets.
  - Model payment, booking, and ticket states; handle duplicate, delayed, and out-of-order webhooks with idempotency.
  - Use an outbox or equivalent durable handoff for email and provider-side effects; retries must not send duplicate business actions.
  - Protect password reset tokens, enforce role/manager scoping on every relevant route, and generate unpredictable ticket codes with suitable uniqueness.
- **Testing strategy:** Unit tests for domain rules; database integration tests for transaction and concurrency behavior; payment/webhook and notification-worker tests with provider fakes; role/ownership authorization tests; end-to-end tests for register → browse → book/pay → view ticket and manager/admin flows.
- **Comparison:** Baseline candidate. It favors local consistency and speed of delivery over independent deployment and fault isolation; it makes no claim that one process will meet unknown peak scale.

### B. Independently deployed domain microservices

- **Overview:** Split the system into services with owned data and explicit network/event contracts. A plausible initial boundary is Identity, Event Catalog/Manager, Reservation, Payment/Order/Ticket, and Notification. These boundaries should be validated against team ownership and business lifecycle rather than chosen only by story count.
- **Main components:** Web client/API gateway; identity service; event catalog service; reservation service owning capacity and holds; payment/order/ticket service integrating the payment provider and issuing tickets; notification service; each service's datastore; message broker/event transport; operational observability and deployment infrastructure.
- **Critical flow:** The reservation service atomically creates a hold in its own store. An orchestration/workflow or order service requests payment. A signed provider callback updates payment state; an event or command causes ticket issuance only after confirmed payment. Services exchange versioned messages and use idempotent consumers, retries, and compensating actions where cancellation or expiry is allowed.
- **Requirement fit:** All functional areas map to API/event capabilities. Identity handles login, password recovery, and role claims; catalog supports browsing and manager event management; user-facing profile/favourites/history can be APIs or projections. The reservation service is authoritative for capacity; the payment/ticket owner controls paid-ticket issuance. Email notifications are isolated from the purchase request.
- **Advantages:**
  - Services can be scaled, deployed, and fault-isolated independently when there is a real need and clear ownership.
  - Explicit data ownership reduces accidental table coupling.
  - Event-driven notifications and activity propagation can be handled without blocking users.
- **Scalability:** Scale reservation, catalog, identity, and notifications separately according to their loads. This helps when workloads differ significantly, but each service and its datastore/broker path introduces its own capacity and availability limits. It does not remove contention on the authoritative inventory store.
- **Maintenance implications:** Teams can own services independently, but the platform needs continuous work for deployment automation, API/event compatibility, broker operations, tracing, alerting, security policy consistency, and cross-service incident response. Schema and contract changes require coordination or backward compatibility.
- **When another architecture is a better choice:** Prefer a modular monolith if one team is delivering the initial product, throughput is unknown/modest, and local transaction simplicity is valuable. Prefer serverless if elastic execution with managed operations is more valuable than provider portability and the team is comfortable with managed cloud workflows.
- **Disadvantages:**
  - Booking-to-payment-to-ticket is a distributed workflow rather than one local transaction.
  - Requires broker, service deployment, API/event versioning, tracing, alerting, and more complex test environments.
  - A service boundary can make simple profile or event pages require multiple network calls and projections.
  - Independent scaling and team autonomy are benefits only if traffic or organizational needs justify the overhead.
- **Implementation challenges / painful details:**
  - Specify a saga/state machine, timeout/expiry policy, compensation semantics, and user-visible pending states.
  - Use transactional outboxes, idempotency keys, deduplication, dead-letter handling, replay controls, and schema evolution for messages.
  - Avoid distributed locks for capacity; keep inventory authority within the reservation service and make its own writes atomic.
  - Decide how profiles, favourites, and purchase history are joined or projected without cross-database queries.
  - Propagate authenticated identity and enforce authorization consistently across services; design correlation IDs and useful cross-service diagnostics.
- **Testing strategy:** Service-level unit and persistence tests; API/event contract tests; saga tests for success, duplicate callbacks, timeouts, retries, and compensation; integration tests with a broker; end-to-end critical purchase and role flows; resilience tests for provider/broker outages.
- **Comparison with A:** Provides stronger independent deployment, scaling, and failure boundaries, but gives up A's straightforward local transaction and simpler operations. Given no stated traffic/team requirement, its distributed consistency and operations costs are not yet justified by the requirements alone.

### C. Managed serverless and event-driven application

- **Overview:** Deploy the web/API entry point as managed gateway plus short-lived functions/handlers; use a managed workflow and queues for long-running payment and notification work. This is a deployment/execution model, not necessarily a separate business-owned service per function. Keep domain boundaries explicit. Use a transactional relational store (or another store with proven conditional-write semantics) as the authoritative source for capacity and order state.
- **Main components:** Static web client/CDN; API gateway; identity provider or identity functions; handlers for event browsing/management, profiles/favourites, bookings, checkout, and admin actions; relational database; managed workflow/queue; payment-provider adapter and callback endpoint; notification worker and email provider; secrets/monitoring services.
- **Critical flow:** The booking handler validates role and event state, then performs an atomic capacity/hold update in the authoritative database. A durable workflow coordinates payment initiation and waits for a verified callback/event. Idempotent state transitions issue a ticket only on confirmed payment. Queue-driven workers send email and retry transient delivery failures.
- **Requirement fit:** Handlers cover the same visitor, user, manager, and admin journeys. Managed identity can provide authentication while application authorization still enforces manager ownership and admin-only manager creation. Functions can scale request processing, and queue/workflow services support asynchronous email and payment coordination. The authoritative database still must protect capacity and order invariants.
- **Advantages:**
  - No application servers to provision and patch; request handlers can scale elastically.
  - Queues and managed workflows support slow or retryable email/payment tasks.
  - A modest team may operate fewer server processes than in a microservice deployment.
- **Scalability:** Gateway handlers and workers can scale independently with request and queue volume, subject to provider quotas, concurrency controls, and database connection/throughput limits. Autoscaling does not by itself protect finite ticket inventory; conditional writes or transactions remain necessary.
- **Maintenance implications:** The provider operates much of the compute and workflow infrastructure, but the team must maintain infrastructure-as-code, permissions, service limits, alarms, deployment/versioning, workflow definitions, and provider-specific operational procedures. Local simulation may not reproduce cloud behavior exactly.
- **When another architecture is a better choice:** Prefer a modular monolith when portability, straightforward local debugging, or a single coherent transactional workflow outweighs elastic execution. Prefer microservices when independently staffed domains and portable service-level deployment/fault isolation are more important than minimizing managed-service coupling.
- **Disadvantages:**
  - Behavior and deployment become coupled to a cloud provider's gateway, function, workflow, identity, and queue services.
  - Function-level execution does not remove domain complexity or the need for transactions and idempotency.
  - Cold starts, concurrency limits, managed-service quotas, and database connections can affect latency or availability.
  - Local integration testing and portability can be harder than a single-process application.
- **Implementation challenges / painful details:**
  - Prevent connection storms from function concurrency (pooling/proxying and bounded concurrency); choose transaction-safe storage rather than assuming a key-value store fits multi-record invariants.
  - Handle at-least-once queue/workflow delivery, duplicate/out-of-order callbacks, workflow timeouts, retry policies, and payment compensation explicitly.
  - Keep functions small enough to deploy/test but avoid scattering domain rules across many handlers.
  - Configure least-privilege service identities, secrets, callback signature validation, rate limits, alarms, and log correlation.
  - Set and test workflow execution limits, queue visibility/retention, dead-letter replay procedures, and provider quotas.
- **Testing strategy:** Unit tests for domain logic; database transaction tests; handler and workflow integration tests; local/cloud contract tests for identity, queue, and payment callback behaviors; end-to-end critical journeys; load tests for simultaneous reservation attempts and database connection limits; failure/retry tests.
- **Comparison with A and B:** Compared with A, it reduces server administration and can absorb variable request load, but introduces cloud-service behavior and still needs careful database capacity control. Compared with B, it avoids many always-on independently operated service processes and may be simpler for a small team, but still has asynchronous distributed workflow complexity and can create stronger provider dependence. It is not automatically cheaper or more reliable; those depend on workload and provider constraints.

## Qualitative comparison

| Criterion | A. Modular monolith | B. Microservices | C. Serverless/event-driven |
|---|---|---|---|
| Booking/payment consistency | Best starting point for local DB transactions; state machine and idempotency still required | Hardest: distributed workflow and eventual consistency | Local DB transaction for reservation plus asynchronous workflow; provider delivery semantics require idempotency |
| Delivery complexity | Lowest | Highest | Medium; fewer servers but more managed-service configuration |
| Independent scaling / deployment | Limited | Strongest when boundaries and ownership are real | Elastic handlers; independent deployment is possible but may fragment domain logic |
| Scaling ceiling / pressure points | Shared application and database; validate booking contention | Per-service scaling, but inventory datastore and broker can still constrain sales | Function concurrency and provider quotas; database remains a critical limit |
| Maintenance profile | One deployable; internal module discipline required | Highest distributed-system and platform maintenance | Lower server maintenance, more provider-specific configuration and workflow operations |
| Failure isolation | Shared process and release | Strongest service boundaries, with broker/provider failures still cross-cutting | Managed isolation per handler/service; cloud quota and shared datastore remain dependencies |
| Operational burden | One app and database to operate | Highest: services, broker, contracts, observability | Cloud configuration and service limits; lower server maintenance |
| Portability | Usually strongest | Good if using portable infrastructure, but broker/data choices matter | Usually weakest due to managed-provider APIs/workflows |
| Fit based on current evidence | Most conservative baseline | Not justified without scale/team/availability evidence | Plausible if managed-cloud constraints and bursty demand are confirmed |

## Recommendation or decision

- **Current recommendation:** Recommend A (modular monolith) as the proposed initial architecture. Based only on the supplied requirements, it is the lowest-complexity candidate that can preserve booking/payment invariants using a relational transaction. C is a credible alternative if managed cloud deployment and elastic workloads are priorities. B should be preferred if independent scaling, team ownership, or fault isolation is demonstrated to justify the extra distributed-systems burden.
- **Status:** Proposed in ADR-001; not accepted. No stakeholder selection or approval is recorded.
- **Assumptions:** A standard web application, a relational database can be used, a payment provider will expose a callback/webhook or equivalent confirmation, and ticket issuance follows confirmed payment. These are assumptions, not facts in the requirements.
- **What could change the recommendation:** Confirmed high peak concurrency, strict independent availability targets, large/independent teams, a mandated cloud platform, operational capability, data-residency rules, or clarified pre-sale and payment lifecycle policies.

## Discussion update log

- **2026-10-29:** Read only `Tasks/data/EventTicket.txt`; summarized roles, journeys, inferred invariants, and unknowns. Established comparison criteria and described three structurally distinct candidates, their components, flows, requirement fit, benefits, costs, implementation details, and tests. Recorded a provisional fit assessment; no architecture was selected and no ADR was created.
- **2026-10-29 (ADR step):** Expanded all three candidates with scalability, maintenance implications, and situations where an alternative is preferable. Compared their consistency, scaling pressure points, operational burden, and portability. Recommended the modular monolith as the proposed starting point given the missing scale/team constraints, and created ADR-001 with Proposed status; stakeholder approval remains open.

## Open questions and next steps

- Confirm whether stakeholders accept the proposed modular-monolith direction or prefer one of the alternatives.
- How exactly does a pre-sale booking differ from buying a ticket; does it reserve capacity, expire, or require payment?
- Are tickets for fixed-capacity events, and must the system guarantee no overselling during a high-volume on-sale?
- What payment provider and confirmation/refund/chargeback lifecycle must be supported?
- What are expected traffic peaks, availability targets, and recovery expectations?
- What cloud/platform, team size/skills, privacy/compliance, and budget constraints apply?
