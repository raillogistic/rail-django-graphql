Upgrade and Improvement Guide for rail-django-graphql

Purpose: Provide a comprehensive, actionable plan to upgrade and improve this library across security, permissions, reporting/observability, performance, metadata/UX, configuration, and code quality. This guide references concrete files in the repository and suggests step-by-step changes, test coverage, and rollout plans.

Audience: Maintainers and integrators of rail-django-graphql.


1) Scope and Goals
- Harden security at the GraphQL and Django boundary, including robust authorization and input validation.
- Make permissions consistent and visible to clients; ensure field-level and relationship-level filtering reflects user permissions.
- Improve performance: reduce N+1 queries, add safe caching, optimize filters, and tune pagination.
- Enhance reporting/observability: structured logging, audit trails, performance metrics, and health endpoints.
- Improve metadata and GraphQL UX: predictable field order, reverse relationships at the end, polymorphic exclusions, nested form linkage details, and quick search filters.
- Strengthen configuration, code quality, testing, and release processes.


2) Baseline Assessment (current state)
- Generators
  - filters.py includes advanced and enhanced filter generators. Quick search was previously gated; now configured to always include a `quick` filter.
  - queries.py/types.py generate GraphQL fields/types and integrate filter classes.
- Metadata
  - extensions/metadata.py provides comprehensive model and form metadata.
  - Recent changes added: my_permissions, improved field-level permission checks using AuthorizationManager fallback, polymorphic-aware exclusions, declared field order tracking, reverse relationships placed at end of field_order, nested relationships excluded from top-level relationships, and linkage attributes for nested metadata.
- Security Extensions
  - extensions/auth.py, permissions.py, validation.py, rate_limiting.py exist and can be integrated.
  - core/security.py contains managers and factories (AuthorizationManager, get_authz_manager) used in permission checks.
- Schema Builder
  - core/schema.py assembles queries and mutations and integrates security extensions.
- Debugging/Observability
  - debugging and health modules provide hooks and health queries.
- Caching
  - Heavy caching removed in metadata; table cache retained for model table metadata.


3) Security Hardening

3.1 Authentication and Session
- Ensure GraphQL endpoint respects Django auth and session middleware.
- Double-check extensions/auth.py MeQuery returns minimal, safe user information.

3.2 Authorization (RBAC and ABAC)
- Centralize field/object permission checks via AuthorizationManager (core/security.py):
  - Use get_authz_manager() in extensions/metadata.py permission checks consistently.
  - In `_has_field_permission`, first check field-level permission via AuthorizationManager; fallback to model-level view permissions.
- Add object-level permission checks in list and single queries:
  - Modify generators/queries.py to apply per-object permission filters (e.g., via a manager or AuthorizationManager query hooks) where applicable.
- Enforce GraphQL authorization in resolvers:
  - In core/schema.py, ensure resolvers created through generators utilize permission checks, especially for mutations.

3.3 GraphQL Security Controls
- Add depth and complexity limits:
  - Implement query depth and cost analysis (debugging/query_analyzer.py). Enforce limits via middleware or resolver wrappers.
- Rate limiting:
  - Ensure extensions/rate_limiting.py queries are included; configure sensible defaults per user/IP.
- Disable introspection in production (optional):
  - Add a schema setting flag (SchemaSettings) for disabling introspection based on environment.

3.4 Input Validation and Sanitization
- Ensure extensions/validation.py hooks are invoked for mutations and filters.
- Add strict validation schemas for mutations in generators/mutations.py and metadata.
- Validate `quick` filter inputs (length cap, whitespace cleanup) to mitigate expensive searches.

3.5 Transport Layer and CSRF
- Confirm GraphQL views (views/graphql_views.py) either:
  - Use CSRF for session-authenticated calls; or
  - Explicitly exempt CSRF if using tokens and document the approach in README_SECURITY.md.

3.6 Secrets and Dependencies
- Move secret-like configs to environment variables; never hardcode.
- Regularly update dependencies (requirements.txt, requirements-optional.txt) and run SAST/DAST.
- Pin versions and add Dependabot/GitHub Actions security scans.

Action Steps:
- [extensions/metadata.py] Normalize usage of AuthorizationManager in all field/relationship checks.
- [generators/queries.py] Introduce object-level permission filters via AuthorizationManager hooks.
- [core/schema.py] Add query depth/complexity checks and integrate rate limiting.
- [views/graphql_views.py] Document and enforce CSRF/token strategy.
- [README_SECURITY.md] Update with new controls, limits, and examples.


4) Permissions Model and Exposure

4.1 Client-visible permissions
- Confirm `my_permissions` are included in ModelFormMetadata (extensions/metadata.py) and reflect Django model permissions (add/change/delete/view) and any custom permission levels.
- Provide a GraphQL field in ModelFormMetadataType to expose `my_permissions` arrays consistently.

4.2 Field/Relationship Filtering
- Continue to filter form_fields and form_relationships using `_has_field_permission`.
- Ensure `field_order` reconciles only permitted fields.
- Expose `has_permission` boolean per field/relationship metadata.

4.3 Configuration
- Add project-level settings to toggle strict permission enforcement modes (e.g., hide unauthorized vs mark readonly) in conf.py/settings.

Action Steps:
- [extensions/metadata.py] Validate that all field/relationship permissions align with AuthorizationManager outputs; add unit tests.
- [docs/metadata-schema-guide.md] Document how permissions influence metadata and UI visibility.


5) Performance Optimization

5.1 Query Efficiency
- In generators/queries.py and types.py, ensure list queries apply select_related/prefetch_related where appropriate.
- Introduce a simple DataLoader pattern for resolving related objects to avoid N+1 in GraphQL resolvers.

5.2 Caching Strategy
- Reintroduce safe, targeted caching:
  - Keep table metadata cache (already present).
  - Consider short-lived caches for form metadata keyed by user, app, model; invalidate on model change.
  - Use settings to control TTLs.

5.3 Filter Performance
- Use indexes for frequently filtered fields; consider db column indexes for `quick` filter candidate fields.
- Cap `quick` filter input length; avoid full-table scans for very large models; consider trigram or full-text indexes if PostgreSQL.
- Provide grouped filters (already in EnhancedFilterGenerator) and document performance trade-offs.

5.4 Pagination and Limits
- Enforce sensible default page sizes in queries.py.
- Support cursor-based pagination for large datasets.
- Add max limits to reverse relationship count filters.

5.5 Profiling and Monitoring
- Use debugging/performance_monitor.py to track query execution time; log slow queries.
- Add metrics (extensions/performance_metrics.py) for request throughput, latency, error rate.

Action Steps:
- [generators/queries.py] Add select_related/prefetch patterns; support DataLoader.
- [extensions/metadata.py] Add lightweight caches with invalidation hooks.
- [generators/filters.py] Cap `quick` filter input, optionally use Postgres optimizations.
- [docs/performance.md] Create a guide for tuning performance.


6) Reporting and Observability

6.1 Structured Logging
- Standardize log format and levels across modules.
- Ensure sensitive data is not logged.

6.2 Audit Trails
- Use extensions/audit.py to record key security events (auth, permission denials, mutation operations).
- Add correlation IDs per request; propagate via logs.

6.3 Health Endpoints
- Confirm extensions/health.py queries are integrated; expose uptime, DB status, cache health.

6.4 Error Tracking
- Hook debugging/error_tracker.py into GraphQL error pipeline.

Action Steps:
- [core/schema.py] Ensure health queries are part of the root Query; confirm resolver binding.
- [extensions/audit.py] Expand with mutation audit entries; Add configuration flags.
- [docs/extensions/README.md] Document audit and health setup.


7) Metadata and GraphQL UX Improvements

7.1 Model Form Metadata
- Ensure field_order follows declaration order with reverse relationships appended last.
- Enforce polymorphic exclusions for parent/child pointers and specified fields (e.g., report_rows, stock_policies, stock_snapshots).
- Exclude nested relationships from top-level relationships to prevent duplication.
- Provide linkage attributes on nested entries: field_name, relationship_type, to_field, from_field, is_required; retain `name` for compatibility.
- Filter `fields` and `relationships` by permissions; reconcile `field_order` accordingly.

7.2 Table Metadata and Filters
- Expose grouped filters via EnhancedFilterGenerator; ensure `quick` filter is always present.
- Document filter schema in docs/metadata-schema-guide.md.

7.3 Schema Consistency
- Normalize naming conventions; ensure pluralization is consistent for list queries.
- Provide deprecation paths for renamed fields (e.g., keep `name` as deprecated while using `field_name`).

Action Steps:
- [extensions/metadata.py] Verify all above behaviors; add tests in tests/unit/test_metadata_schema.py.
- [generators/filters.py] Ensure `quick` filter appears for all filter sets; add tests in tests/unit/test_generators.py.


8) Configuration and Settings
- Use SchemaSettings for feature toggles: enable_pagination, generate_filters, depth limits, rate limiting, quick filter behavior.
- Expose settings in conf.py and core/settings.py; support multi-schema via registry integration.
- Provide defaults in defaults.py and document overrides in docs.

Action Steps:
- [core/settings.py, conf.py] Add flags for security limits, quick filter behavior, and caching TTLs.
- [README.md] Update configuration section with examples.


9) Code Quality and Standards
- Adopt consistent type hints and docstrings (already prevalent).
- Enforce pre-commit hooks: black, isort, flake8, mypy.
- Keep functions concise; prefer composition over large monoliths.
- Add lint and test jobs to GitHub Actions (workflows/lint.yml, ci.yml).

Action Steps:
- [setup.cfg, .pre-commit-config.yaml] Ensure code style tools are configured.
- [tests/] Increase coverage to at least 80%; critical functions to 95%.


10) Testing Strategy
- Unit tests: metadata extraction, permission checks, filter generation (including quick), query generation, mutations.
- Integration tests: schema building, basic queries/mutations, auth flows.
- Performance tests: large models/lists, quick search heavy inputs.
- Security tests: authorization failures, rate limits, validation errors.

Action Steps:
- [tests/unit/] Add tests for `_has_field_permission`, polymorphic exclusions, reverse field ordering, nested relationship exclusion.
- [tests/integration/] Add end-to-end tests for schema and filters.


11) Release and Versioning
- Follow semantic versioning; update CHANGELOG.md for each change set.
- Provide migration notes in RELEASE_MANUAL.md when fields or behaviors change.
- Tag releases and automate publishing via .github/workflows/release.yml.


12) Step-by-Step Implementation Plan (Phased)

Phase 1: Security & Permissions (Weeks 1–2)
- Integrate AuthorizationManager consistently in metadata and queries.
- Add query depth/complexity limits and rate limiting; update README_SECURITY.md.
- Ensure CSRF/token strategy is documented and enforced.
- Tests: unit + integration for permission paths and security limits.

Phase 2: Performance (Weeks 2–3)
- Add select_related/prefetch_related in queries.
- Introduce a simple DataLoader pattern in resolvers.
- Reintroduce targeted caching for form metadata with TTL and invalidation.
- Tests: performance benchmarks and regressions.

Phase 3: Metadata & UX (Week 3)
- Finalize field_order logic; verify reverse relationships end placement.
- Confirm polymorphic exclusions and nested exclusions.
- Ensure linkage attributes in nested metadata and deprecation of `name` is documented.
- Tests: metadata unit tests.

Phase 4: Observability & Reporting (Week 4)
- Hook audit trails for mutations and permission denials.
- Integrate performance metrics and health queries.
- Standardize logging format and correlation IDs.
- Tests: audit and health integration.

Phase 5: Documentation, CI/CD, and Release (Week 4)
- Update docs across usage, metadata schema, security recommendations.
- Improve CI with linting + tests + security scans.
- Prepare release notes and migration guidance.


13) Rollback Plan and Risk Mitigation
- Use feature toggles to disable new behaviors if regressions occur (depth limits, rate limiting, quick filter auto-detect).
- Maintain backward-compatible GraphQL fields (e.g., `name`) until a major version change.
- Keep detailed changelog and migration guides.


14) Appendix

14.1 Example Quick Filter Usage
Query (with quick):
```
query {
  products(filter: { quick: "abc" }) {
    id
    name
  }
}
```

14.2 Example Model Form Metadata Fields
- field_order respects model declaration order; reverse relationships appended last.
- `nested` entries include: field_name, relationship_type, to_field, from_field, is_required (and deprecated `name`).

14.3 Settings Snippet
```python
# core/settings.py
class SchemaSettings:
    enable_pagination: bool = True
    generate_filters: bool = True
    enable_rate_limiting: bool = True
    max_query_depth: int = 6
    max_query_complexity: int = 100
    disable_introspection_in_prod: bool = False
    form_metadata_cache_ttl_seconds: int = 600
```

14.4 Test Checklist
- Unit: permissions, metadata ordering, quick filters, validation, rate limits.
- Integration: schema generation, query/mutation flows.
- Performance: large dataset queries; quick search bounds.
- Security: denial cases, CSRF/token handling consistency.


Concluding Note
This guide is intended to be pragmatic and incremental. Each phase provides concrete, testable improvements. As new requirements emerge (e.g., multi-tenant support, persisted queries, async IO), adapt the plan and document accordingly.