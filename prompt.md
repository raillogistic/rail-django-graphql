Title: Build an advanced table-filtering UI powered by the GraphQL filtering system

Role: You are an AI agent tasked with building a production-grade, advanced UI for
data-table filtering. The backend provides a GraphQL filtering system implemented in:
- rail_django_graphql/generators/filters.py
- rail_django_graphql/generators/queries.py

Goal
- Create a robust, user-friendly filtering experience for tabular data that fully
  leverages the GraphQL filter capabilities (basic and complex) and supports nested
  relations, multiple field types, and advanced operations.

Key backend facts to rely on
- The AdvancedFilterGenerator and EnhancedFilterGenerator produce filter operations
  per field type (text, numeric, date/datetime, boolean, foreign key, many-to-many,
  choice, file, json). Each operation carries a lookup_expr (e.g., exact, icontains,
  range, in) and an optional description/help text.
- QueryGenerator exposes two query styles:
  1) generate_list_query(model) with basic filter arguments (from FilterSet base_filters)
     and a complex "filters" argument for nested boolean logic.
  2) generate_paginated_query(model) with similar filters and returns items + page_info.
- Ordering, offset/limit (or pagination), and advanced nested filtering are supported.
- Model table metadata (modelTable) includes fields and grouped filter options with
  per-field operations. Use it to drive the UI.

Deliverables
1) A reusable filtering UI component suite (React + TypeScript preferred) that:
   - Allows end-users to create, edit, and apply complex filters with AND/OR/NOT groups.
   - Supports nested field selection (e.g., customer__name__icontains) with max depth
     consistent with backend limits.
   - Maps UI controls to backend filter operations derived from metadata and/or
     EnhancedFilterGenerator grouped filters.
   - Handles basic filter arguments (FilterSet base_filters) and complex filters via the
     backend ComplexFilterInput. Use GraphQL variables, do not inline values in query
     strings.
   - Integrates ordering, pagination/offset-limit, and shows live result counts if
     available without excessive requests.
   - Provides preset management (save, load, rename, delete, share via URL params).
   - Includes accessibility (keyboard navigation, ARIA labels) and i18n hooks.

2) GraphQL client layer:
   - A typed client (e.g., Apollo Client or urql) with generated types (codegen) for:
     - modelTable metadata query (fields and filters)
     - list and paginated queries for the target model
   - A mapper that transforms the UI filter state into GraphQL variables for both basic
     filters (FilterSet base_filters) and complex nested filters.
   - Debounced network requests on filter changes; cancel in-flight requests when
     superseded.

3) Documentation:
   - Brief README explaining how to use the components, configure endpoints, and map
     model metadata to UI controls.
   - Examples demonstrating common filter scenarios.

4) Tests:
   - Unit tests (Jest) for the UI state manager, filter builders, mappers, and preset
     logic.
   - Integration tests against a mocked GraphQL API for basic and complex filters,
     pagination, ordering, and nested fields.

Core UI requirements
- Filter bar: quick text search, open advanced filter builder, clear-all, preset
  dropdown.
- Advanced filter builder:
  - Group composer with AND/OR/NOT toggles.
  - Field selector sourced from model metadata (including nested fields where
    supported). Show related_model info if available.
  - Operation selector based on the selected field type and supported operations
    (e.g., text: exact, icontains, startswith; numeric: gt/gte/lt/lte/range; date:
    exact, range, today/this_week/this_month/this_year; boolean: exact/isnull;
    foreign key: exact/in/isnull; m2m: in/count_*; choice: exact/in).
  - Value editor tailored to the operation type (text input, number, date range picker,
    checkbox, multi-select, tag chips for arrays).
  - Validation feedback (e.g., arrays required for "in", date ranges require two
    values).
  - Preview of the resulting GraphQL variables payload.

- Table and results:
  - Fetches via list or paginated query with variables: filters, order_by, offset/limit
    (or page/per_page), and basic filter args.
  - Displays current applied filters as removable chips.
  - Allows ordering with a multi-column selector; uses backend annotations for count
    ordering when requested (see queries.py implementation).

GraphQL contracts to use
- Model table metadata (example, adjust names if different in schema):

  query GetModelTable($app: String!, $model: String!) {
    modelTable(app: $app, model: $model) {
      verboseName
      fields {
        name
        title
        helpText
        filterable
        sortable
      }
      filters {
        field_name
        is_nested
        related_model
        is_custom
        options {
          name
          lookup_expr
          help_text
          filter_type
        }
      }
    }
  }

- List query (non-Relay) typical usage with both basic and complex filters:

  query ListItems(
    $filters: ComplexFilterInput
    $order_by: [String!]
    $offset: Int
    $limit: Int
    $basic: BasicFiltersInput
  ) {
    listItems(
      filters: $filters
      order_by: $order_by
      offset: $offset
      limit: $limit
      # Spread basic filter variables based on FilterSet base_filters (generated per model)
      # E.g., name__icontains: $basic.name__icontains, status__exact: $basic.status__exact
    ) {
      id
      ...TableFields
    }
  }

  Note: The exact shape of ComplexFilterInput and BasicFiltersInput comes from
  AdvancedFilterGenerator.generate_complex_filter_input(model) and
  generate_filter_set(model). Use GraphQL introspection or codegen to derive input
  types. Do not hardcode field names; source them from metadata and introspection.

Mapper guidelines (UI -> GraphQL variables)
- Basic filters:
  - For each selected basic operation, set variables matching FilterSet base_filters
    names (e.g., name__icontains, created_at__range, status__in).
- Complex filters:
  - Compose a tree structure with logical groups (AND/OR/NOT) referencing
    field paths and lookup_expr from metadata options.
  - Example conceptual payload (illustrative; confirm exact input fields via
    introspection):
    {
      filters: {
        and: [
          { field: "name", op: "icontains", value: "rail" },
          {
            or: [
              { field: "status", op: "exact", value: "active" },
              { field: "status", op: "exact", value: "pending" }
            ]
          },
          { field: "customer__name", op: "icontains", value: "john" }
        ]
      }
    }

Architecture and components
- React + TypeScript, Vite or Next.js.
- State management: lightweight (React Context) or Redux Toolkit if needed.
- Components:
  - FilterBar
  - FilterBuilder (with Group, Condition, FieldSelector, OperationSelector,
    ValueEditor)
  - FilterChipList
  - PresetManager
  - TableView
  - GraphQLClientProvider
  - IntrospectionService (fetches metadata and input types for filters)

UX details
- Debounce filter application (250–500ms) to avoid chatty requests.
- Show skeletons/spinners during fetch; error toasts on failure.
- Persist last-used filters and presets to localStorage; provide import/export JSON.
- Accessible keyboard navigation within builders and lists.

Performance & resilience
- Use GraphQL variables and codegen types; prefer cursor-based pagination if Relay
  is enabled, else offset/limit.
- Cancel stale requests when filters change quickly.
- Avoid N+1 selections; rely on backend optimizations present in queries.py.

Security & correctness
- Validate all user inputs before mapping to variables (arrays for "in", ranges must
  be [min, max], booleans where required).
- Do not build raw query strings from user input; always use variables.
- Sanitize values displayed in the UI (escape HTML where applicable).

Testing requirements
- Jest + React Testing Library.
- Unit tests: mapper functions, condition builders, preset serialization.
- Integration tests: mocked GraphQL responses for basic and complex filter flows,
  ordering, pagination.
- Coverage target: 80% overall, 95% for critical mapping functions.

Output expectations
- Provide a minimal runnable example with a mock GraphQL endpoint and realistic
  input types derived via introspection.
- Include README with setup, metadata query usage, and examples.
- Provide typed GraphQL operations and a small codegen setup (e.g., GraphQL Code
  Generator) to ensure input/output types are enforced.

Notes
- Respect backend limits on nested depth (DEFAULT_MAX_NESTED_DEPTH and
  MAX_ALLOWED_NESTED_DEPTH in filters.py).
- If metadata filters are empty for a model, gracefully degrade by offering basic
  operations inferred from field types (text: exact/icontains; numeric: exact/gt/gte/
  lt/lte; date: exact/range/today/this_month/this_year; boolean: exact/isnull; FK:
  exact; M2M: in). Confirm against model metadata and introspection.

Success criteria
- The filtering UI is intuitive, powerful (supports complex logic and nesting),
  accessible, and robust against malformed inputs.
- Queries execute with correct variables and return expected results.
- Documentation and tests are complete and easy to follow.