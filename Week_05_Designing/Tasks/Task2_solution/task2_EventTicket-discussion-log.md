# EventTicket discussion notes — ongoing log

> This log starts with the ADR task. It intentionally does not recap the earlier architecture discussion.

## 2026-10-28 — Creating the architecture decision record

- Created a proposed ADR for the initial EventTicket architecture.
- Recorded a modular monolith as the recommended starting point, with the status marked **Proposed** because no explicit stakeholder approval or operational constraints were established.
- Captured the decision's assumptions, decision drivers, consequences, safeguards, and alternatives; the revisit and validation sections were subsequently removed at the user's request.
- Created the ADR at [ADR-001-event-ticketing-architecture.md](./ADR-001-event-ticketing-architecture.md).
- Added a Mermaid component/dependency diagram to the ADR showing the web UI, modular application, relational database, durable background work, worker process, and payment/email providers.
- Clarified that the diagram is logical rather than provider-specific, and that web and worker processes may use the same codebase.
- Renamed the ADR heading to "ADR-001: Decision to Choose an Architecture for the EventTicket Project."
- Added a potential-stakeholders section to the ADR, covering users/attendees, managers, admins, product/business, development and operations teams, external providers, and security/privacy/compliance roles. The document explicitly notes these groups are not confirmed project participants.
- Consolidated the stakeholder summary into Context, removed the architecture-options list from Context so alternatives are presented only under "Alternatives considered," and changed the Decision wording to "We will use a modular monolith." ADR status remains Proposed pending stakeholder approval.
- Removed the "Revisit this decision when" and "Validation plan" sections from the ADR as requested.
- Added explicit pros and cons for the chosen modular monolith and for both alternatives (microservices and serverless/event-driven).
- Added a distinct Consequences section listing positive outcomes and potential drawbacks across technical, operational, and business impacts.
- Reordered the ADR so Consequences immediately follows the full trade-off discussion for the chosen architecture and alternatives; implementation safeguards now follow Consequences.

## Further discussion

- Add new decisions, clarifications, and follow-up actions here as the discussion continues. Do not backfill the earlier conversation.
