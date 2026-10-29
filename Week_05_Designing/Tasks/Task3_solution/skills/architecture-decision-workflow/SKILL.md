---
name: architecture-decision-workflow
description: "Analyze software requirements, identify architectural drivers and quality attributes, generate and explicitly compare architecture candidates, recommend a fit, create or update an ADR, and maintain structured discussion notes. Use for architecture discussions, architecture selection, solution evaluation, and ADR creation or revision."
argument-hint: "Describe the system, requirements, candidate architectures, or ADR/notes to create or update."
user-invocable: true
---

# Architecture Decision Workflow

Use this skill to take a software architecture discussion from requirements through candidates, comparison, recommendation, and an Architecture Decision Record (ADR), while maintaining a concise, persistent record of the discussion.

## Principles

- Ground analysis in the supplied requirements and constraints. Do not invent requirements, stakeholder approval, architecture facts, service-level objectives, costs, or traffic estimates.
- Distinguish **stated facts**, **reasonable assumptions**, and **unknowns**. Label assumptions and open questions; ask the user when an unknown could materially change the recommendation.
- Architecture styles are candidates, not goals. Prefer the least complex option that adequately satisfies the important requirements, while acknowledging when evidence is insufficient.
- Compare candidates against the same criteria. Explain the reasons behind judgments instead of presenting unsupported scores.
- Describe the whole system at the requested level. Identify key components, ownership/boundaries, external dependencies, and critical data flows.
- Treat operational concerns, failure modes, security/privacy, and business impact as part of architecture, not as afterthoughts.
- Keep recommendations and decisions distinct. Do not mark an ADR Accepted or imply stakeholder approval unless the user or reliable project evidence establishes that approval.
- In an ongoing discussion, update the notes at each substantive step. Preserve existing user-authored material and follow instructions about whether to backfill earlier conversation.
- Be responsive to the requested depth. Do not force a full ADR or exhaustive analysis into an exploratory question unless asked.

## Workflow

### 1. Establish scope and inspect source material

1. Identify the system, requested outcome, expected audience, and whether the user wants a proposal, a detailed analysis, a recommendation, or an ADR.
2. Locate and read only the requirements, prior notes, ADRs, or other sources relevant to the request. Confirm exact filenames before relying on them.
3. If an existing discussion or ADR is being continued, read it first. Preserve its structure and prior decisions unless asked to change them.
4. If the note/ADR destination is unspecified, use a reasonable workspace location when the request clearly implies a repository deliverable; ask if scope, sharing, or overwrite risk is material. Never overwrite an existing artifact without inspecting and integrating it.
5. Ask focused questions only for decision-critical gaps (for example, required availability, regulatory/data-residency restrictions, expected scale, team capability, or budget). If the user prefers to proceed, record assumptions and continue.

### 2. Analyze requirements

Build a compact requirements baseline:

- **Actors and stakeholders:** users, operators, administrators, business owners, external providers, and affected parties implied by the material. Mark inferred stakeholder groups as potential, not confirmed.
- **Functional capabilities:** group user stories or requirements by domain; preserve their intent and identify actors/permissions.
- **Critical journeys:** outline workflows with meaningful cross-component effects (for example, reserve → pay → issue ticket).
- **Business invariants:** identify rules that must remain true, such as no overselling, ownership boundaries, or issuing a ticket only for confirmed payment.
- **Quality attributes:** derive relevant attributes such as correctness/consistency, security/privacy, availability, performance, scalability, modifiability, usability, testability, and operability.
- **Constraints and uncertainties:** record known platforms, integrations, team and operational constraints, plus policy decisions not specified.

Do not treat quality attributes as confirmed requirements merely because they are common. Label each as **stated**, **inferred**, or **unknown**, and explain what requirement or workflow makes it relevant. Prioritize drivers (for example, high/medium/low) only when evidence supports the priority.

### 3. Generate architecture candidates

Propose the number requested. If the user asks for an initial set but gives no count, provide three meaningfully different candidates. Make distinctions structural, such as:

- a modular monolith with clear in-process modules and a shared transactional store;
- independently deployed services with explicit data ownership and API/event integration;
- a managed/serverless, event-driven design with functions, queues, and workflow orchestration.

Do not assume these examples fit every system. Tailor or replace them based on requirements. Avoid superficial variations (such as three technology stacks for the same structure). Briefly state each candidate's organizing idea, key boundaries, and primary trade-off.

### 4. Compare candidates with explicit criteria

Choose criteria that trace to the prioritized drivers. Common criteria include:

- functional coverage and ability to preserve business invariants;
- consistency and transaction complexity;
- performance and scaling characteristics;
- availability, failure isolation, and resilience;
- security, privacy, and data ownership;
- development complexity and time to deliver;
- operations, observability, and incident response;
- team fit, deployability, and independent ownership;
- cost profile, provider coupling, and reversibility;
- testability and evolution/modifiability.

Use a comparison table when it improves clarity. For every candidate, state its relative fit and the reason. If using numeric weights/scores, explain the scale and the evidence; do not imply precision unsupported by the inputs. If priorities are unknown, use a qualitative comparison and identify which unknowns could change the result.

For each candidate, include the requested level of:

- high-level overview and component boundaries;
- critical data flow(s), especially cross-boundary flows;
- how it satisfies the functional requirements and key quality attributes;
- advantages and disadvantages;
- bottlenecks and likely failure pressure points;
- hardest implementation details and operational concerns;
- appropriate testing strategy.

In a multi-turn discussion, expand one candidate at a time when asked, then explicitly compare it with previously examined candidates. Avoid repeating entire earlier sections; focus on the new trade-offs and update the persistent notes.

### 5. Recommend an architecture

1. State the best fit for the current evidence and connect it to the prioritized drivers.
2. Explain the material trade-offs and the strongest reason not to choose it.
3. State assumptions that support the recommendation and the open questions most likely to change it.
4. If the user has selected an option, reflect their selection accurately. Do not substitute a different choice without explaining a material concern.
5. Keep recommendation language separate from decision status. A recommendation is not stakeholder approval.

### 6. Explain a selected architecture at the requested depth

When asked to examine a candidate in detail:

1. Draw its component structure using readable ASCII or Mermaid. Show trust/external-system boundaries and data stores where useful.
2. Walk through the important workflows in ordered steps. Include synchronous and asynchronous paths, ownership, and failure/retry behavior where material.
3. Identify bottlenecks using concrete pressure points (such as contention, hot data, connection limits, queues, provider latency, or shared runtime resources).
4. Describe the hardest implementation work, including edge cases and unspecified policy choices.
5. Recommend a layered test strategy appropriate to the architecture:
   - unit/business-rule tests;
   - database or persistence integration tests;
   - API/module/event contract tests as applicable;
   - provider/webhook and background worker tests;
   - end-to-end critical journeys;
   - concurrency, load, resilience, and security tests where relevant.
6. Compare against the previously discussed candidates using consistent criteria.
7. Add newly discovered assumptions, risks, and unanswered questions to the notes.

### 7. Maintain structured discussion notes

Create or update a persistent Markdown notes file when requested or when the user has established ongoing notes. Use the template at [discussion-notes-template.md](./references/discussion-notes-template.md).

- Update notes throughout the discussion, not only at the end.
- Record each meaningful step: requirement findings, drivers, proposed candidates, comparisons, deeper analysis, user clarifications, recommendation/selection, ADR edits, and open questions.
- Prefer concise summaries over verbatim transcripts.
- Do not backfill earlier conversation when the user says notes should start now; record that boundary.
- When a notes file already exists, append/update the relevant section without discarding user edits or unrelated content.
- Ensure notes describe what was actually done; do not claim a file was created or updated until verified.

### 8. Create or revise the ADR

Create or update the ADR only when requested or when the discussion reaches the requested decision-record step. Use [adr-template.md](./references/adr-template.md) as the default structure.

Include, as appropriate:

- decision identifier/title, status, and date;
- **Context:** system purpose, relevant requirements/drivers, concise potential stakeholders, assumptions, and constraints. Do not repeat the list of architecture options here if they appear in Alternatives;
- **Decision:** clear, direct wording (for example, “We will use …”) and the selected architecture at useful detail;
- a visual architecture representation when requested or helpful;
- explicit trade-offs for the chosen option;
- alternatives considered, each with both pros and cons;
- **Consequences:** positive outcomes and potential drawbacks across technical, operational, and business impacts;
- implementation constraints/safeguards when relevant.

Keep alternatives in one place rather than listing them in Context and repeating them later. Preserve requested section ordering and edits; do not re-add sections the user explicitly removed. Mark status **Proposed** (or equivalent) when approval is not evidenced. Use **Accepted** only when the user confirms the decision or the source clearly records approval. Link related notes and ADRs with relative links inside documents.

### 9. Verify and report

- Re-read the edited files or inspect the exact changed ranges.
- Confirm headings, frontmatter (for this skill), Mermaid/code fences, links, status, and required sections are present and coherent.
- Ensure the note log records the latest action.
- Report the created/updated files with workspace links and a concise summary of the outcome. State any assumptions or validation not performed.

## Deliverable references

- ADR structure: [adr-template.md](./references/adr-template.md)
- Ongoing discussion log: [discussion-notes-template.md](./references/discussion-notes-template.md)
