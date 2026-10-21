# Software Requirements

## Priority Scale

- **High:** Essential or blocking functionality; required for a viable system.
- **Medium:** Important functionality, but not blocking the core system.
- **Low:** Desirable or optional functionality that can be deferred.

## Accepted Requirements

### REQ-001: Material Volume Reporting

- **Priority:** High
- **Source documents:** `conversations/conv_pines014_material_volume.eml`, `early_draft_srs_galecia.txt`, `interview_cataloging_2009-05-08.txt`

Provide a consolidated material volume reporting capability for a specified library location that presents a single view as of a chosen point in time, including the total item count scoped to the library location. The report must show separate counts for acquisitions (new items), on-shelf items (in-library), and items in circulation (checked out), plus a combined total. It should break counts down by categories (for example fiction vs non-fiction, format, and other locally defined groupings such as adult fiction or board books) and include a category-level breakdown of holds (total and by category). Libraries must be able to customize which categories are used for breakdowns. The report must support point-in-time and historical filtering (for example volume added in the last 30/60/90 days) leveraging acquisition dates where applicable, and the query must scope items where the item location equals the selected library location so staff can produce a single exportable view without navigating across multiple screens. All sources and date scopes should be combined in the final report output.

### REQ-002: System Capacity Overview and Branch Drill-Down

- **Priority:** High
- **Source documents:** `conversations/conv_pines015_capacity_interface.eml`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`

Provide a system-wide capacity overview dashboard that displays capacity information for all library locations, including high-level per-branch key metrics (e.g., current occupancy, capacity value, percent full). Support drill-down into individual branch details with the full set of capacity metrics and historical/trend data. Backend aggregation must pull data from a centralized database to ensure up-to-date information. The interface must handle large numbers of locations (hundreds of branches) with grouping, filtering, aggregation, pagination, and sorting; support exporting to CSV and displaying trend visuals. Users should be able to filter by region/system, library type, and current load, with configurable thresholds for color-coded capacity states (e.g., under/approaching/over capacity).

### REQ-003: Shelf Space and Genre/Format Reporting

- **Priority:** High
- **Source documents:** `conversations/conv_pines016_shelf_space.eml`, `early_draft_srs_galecia.txt`, `interview_cataloging_2009-05-08.txt`

Provide shelf-space and circulation analytics by genre and format, computing three percentages for each genre/format: (a) percentage of total circulations, (b) percentage of the collection, and (c) percentage of total shelf space. The report must operate at both per-library and system-wide aggregation, count raw figures (items by genre/format and checkouts by genre/format), and support date-range filtering for period comparisons. Because explicit shelf-space data may be unavailable, estimate shelf space from available data with a documented fallback (for example using item counts) and record the estimation method with the outputs. The system must also provide local versus system-average comparisons and a side-by-side multi-library view for selected libraries, with adjustable grouping controls (group by genre, by format, or by both).

### REQ-004: Patron Demographics and Inactivity Analytics

- **Priority:** High
- **Source documents:** `conversations/conv_pines023_patron_characteristics.eml`, `conversations/conv_pines024_inactive_patrons.eml`, `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`, `survey_results_2009.txt`

Provide rich patron analytics with filtering and grouping by demographics (age range, zip code, county, home library, patron type, and preferred language) using LIMIT and GROUP BY, with combinable boolean filters. Age must be computed from birth_date using configurable brackets, and records with null/missing demographic values must appear in results. Support aggregations by demographics (counts and circulation), activity-based filters (e.g., inactivity windows) combinable with demographics, and configurable inactivity thresholds with common presets (30/90/180/365 days) plus custom values. Outputs should be exportable to CSV, support background processing and caching for large datasets, and provide outreach-ready output including current mailing address. Include options to flag patrons with outstanding fines, support on-demand and scheduled runs, and scale for large consortia while anonymizing data for privacy. The system should enable joining patron and item financial data, track inactivity across multiple data sources, provide configurable scope (system/home library/county), and include outreach-ready output.

### REQ-005: Financial Reporting, Accounting, and Patron/Item Integration

- **Priority:** High
- **Source documents:** `email_financial_reports.eml`, `email_report_features.eml`, `email_staff_login.eml`, `evergreen_reference_2009.txt`

Consolidate financial reporting capabilities to include reports on the value of items (based on purchase price), patron account balances by patron/home library/system, and fines/charges accrued by time period and type. Track fines waived by time period and by library branch; provide payments reporting by time period, method, and location; maintain an auditable payment-to-charge ledger and support compliance with data retention policies. Enable joining patron and item financial data for combined views (payments/charges tied to specific patrons and items), support real-time balance updates, maintain configurable transaction histories with retention policies, and provide revenue and aging analytics dashboards suitable for governance oversight.

### REQ-006: Reporting Tooling, Templates, Permissions, and Admin UI

- **Priority:** High
- **Source documents:** `email_report_features.eml`, `evergreen_reference_2009.txt`, `meeting_minutes/meeting_2009-03-15_minutes.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

Offer a comprehensive reporting framework including a user-friendly query design interface for all record types (bibliographic, item, patron, transaction, financial) with field pickers, regular-expression matching, and Boolean operators; display the query criteria with results; provide report templates (canned and open templates) with cloning and restrictions on editing; implement fine-grained permissions and shared folders to control access; ensure queue visibility, prioritization, and support for running multiple reports concurrently. Include predefined boards/executive reports and cross-tabulation templates, data quality and audit reporting, and open-template reporting for ad hoc needs. Provide context-sensitive online help, and robust error reporting.

### REQ-007: Security, Access Control, and Interoperability

- **Priority:** High
- **Source documents:** `email_staff_login.eml`, `evergreen_reference_2009.txt`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

Implement role-based access control with security groups/roles and session-based permission enforcement at login. Support traditional username/password authentication and optional streamlined methods (e.g., card swipe) while preserving auditable staff identity. Ensure the reporting module is isolated from OPAC to prevent performance degradation, support separate development, training, and production environments with configuration/template migration, and provide read-only interaction with ILS/OPAC data. Enable interfacing with vendor systems via APIs or standard data formats (e.g., USMARC21, EDIFACT). Deliver accessible, standards-compliant HTML output with cross-browser support and Section 508 accessibility. The architecture should be multi-location, centralized, and scalable, with a data dictionary and data definitions deliverable, and allow migration of configurations between environments.

## Discarded Requirements

No requirements were discarded.
