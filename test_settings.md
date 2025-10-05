# Checkable TODO List: Test LIBRARY_DEFAULTS Settings

Use this checklist to verify all settings are correctly applied via the settings proxy (`rail_django_graphql.conf.settings`). Mark each box `[x]` when completed.



## Core Schema Configuration
- [ ] Confirm `settings.DEFAULT_SCHEMA == 'main'`
- [ ] Confirm `settings.GRAPHIQL_TEMPLATE == 'graphene/graphiql.html'`
- [ ] Confirm `settings.SCHEMA_ENDPOINT == '/graphql/'`
- [ ] Confirm nested `SCHEMA_SETTINGS` keys exist
  - [ ] `settings.SCHEMA_SETTINGS['excluded_apps'] == ['admin','auth','contenttypes','sessions']`
  - [ ] `settings.SCHEMA_SETTINGS['excluded_models'] == []`
  - [ ] `settings.SCHEMA_SETTINGS['enable_introspection'] is True`
  - [ ] `settings.SCHEMA_SETTINGS['enable_graphiql'] is True`
  - [ ] `settings.SCHEMA_SETTINGS['auto_refresh_on_model_change'] is True`
  - [ ] `settings.SCHEMA_SETTINGS['enable_pagination'] is True`
  - [ ] `settings.SCHEMA_SETTINGS['auto_camelcase'] is False`

## Authentication and Security
- [ ] Confirm `settings.AUTHENTICATION_REQUIRED is False`
- [ ] Confirm `settings.PERMISSION_CLASSES == []`
- [ ] Confirm `settings.ENABLE_INTROSPECTION is True`
- [ ] Confirm `settings.ENABLE_PLAYGROUND is True`
- [ ] Validate `SECURITY_SETTINGS`
  - [ ] `ENABLE_RATE_LIMITING is False`
  - [ ] `RATE_LIMIT_PER_MINUTE == 60`
  - [ ] `RATE_LIMIT_PER_HOUR == 1000`
  - [ ] `ENABLE_QUERY_WHITELIST is False` and `QUERY_WHITELIST == []`
  - [ ] `ENABLE_QUERY_BLACKLIST is False` and `QUERY_BLACKLIST == []`
  - [ ] `ENABLE_IP_WHITELIST is False` and `IP_WHITELIST == []`
  - [ ] `ENABLE_CORS is True`
  - [ ] `CORS_ALLOW_ALL_ORIGINS is False`
  - [ ] `CORS_ALLOWED_ORIGINS == []`

## Queries
- [ ] Validate `QUERY_SETTINGS`
  - [ ] `ENABLE_FILTERING is True`
  - [ ] `ENABLE_ORDERING is True`
  - [ ] `ENABLE_PAGINATION is True`
  - [ ] `DEFAULT_PAGE_SIZE == 20`
  - [ ] `MAX_PAGE_SIZE == 100` (>= default)
  - [ ] `ENABLE_SEARCH is True` and `SEARCH_FIELDS == ['name','title','description']`
  - [ ] `ENABLE_AGGREGATION is True`
  - [ ] `ENABLE_DISTINCT is True`
  - [ ] `ENABLE_RELATED_FIELDS is True`
  - [ ] `MAX_QUERY_DEPTH == 10` (1–50)
  - [ ] `MAX_QUERY_COMPLEXITY == 1000` (1–10000)
  - [ ] `ENABLE_QUERY_COST_ANALYSIS is True`
  - [ ] `QUERY_TIMEOUT == 30` (>0)

## Mutations
- [ ] Validate `MUTATION_SETTINGS`
  - [ ] `ENABLE_CREATE is True`
  - [ ] `ENABLE_UPDATE is True`
  - [ ] `ENABLE_DELETE is True`
  - [ ] `ENABLE_BULK_OPERATIONS is True`
  - [ ] `MAX_BULK_SIZE == 100`
  - [ ] `ENABLE_SOFT_DELETE is False`
  - [ ] `ENABLE_AUDIT_LOG is True`
  - [ ] `ENABLE_VALIDATION is True`
  - [ ] `ENABLE_NESTED_MUTATIONS is True`
  - [ ] `ENABLE_FILE_UPLOADS is True`
  - [ ] `MAX_FILE_SIZE == 10 * 1024 * 1024`
  - [ ] `ALLOWED_FILE_TYPES` equals
    `['image/jpeg','image/png','image/gif','image/webp','application/pdf','text/plain','text/csv','application/json','application/xml']`

## Type Generation
- [ ] Validate `TYPE_SETTINGS`
  - [ ] `ENABLE_AUTO_CAMEL_CASE is True`
  - [ ] `ENABLE_RELAY_NODES is False`
  - [ ] `ENABLE_CUSTOM_SCALARS is True`
  - [ ] `ENABLE_ENUM_CHOICES is True`
  - [ ] `ENABLE_FIELD_DESCRIPTIONS is True`
  - [ ] `ENABLE_MODEL_DESCRIPTIONS is True`
  - [ ] `EXCLUDE_FIELDS == ['password','secret','token']`
  - [ ] `INCLUDE_PRIVATE_FIELDS is False`
  - [ ] `ENABLE_COMPUTED_FIELDS is True`
  - [ ] `ENABLE_REVERSE_RELATIONS is True`
  - [ ] `MAX_RELATION_DEPTH == 3`

## Performance and Caching
- [ ] Validate `PERFORMANCE_SETTINGS`
  - [ ] `ENABLE_QUERY_OPTIMIZATION is True`
  - [ ] `ENABLE_SELECT_RELATED is True`
  - [ ] `ENABLE_PREFETCH_RELATED is True`
  - [ ] `ENABLE_ONLY_FIELDS is True`
  - [ ] `ENABLE_DEFER_FIELDS is False`
  - [ ] `ENABLE_QUERY_CACHING is True` and `CACHE_TIMEOUT == 300`
  - [ ] `ENABLE_RESULT_CACHING is False` and `RESULT_CACHE_TIMEOUT == 60`
  - [ ] `ENABLE_DATALOADER is True` and `DATALOADER_CACHE_SIZE == 1000`
- [ ] Validate top-level caching
  - [ ] `ENABLE_CACHING is False`
  - [ ] `CACHE_BACKEND == 'default'`
  - [ ] `CACHE_TIMEOUT == 300`
  - [ ] `CACHE_KEY_PREFIX == 'rail_graphql'`
  - [ ] `CACHE_VERSION == 1`
  - [ ] `ENABLE_CACHE_INVALIDATION is True`
  - [ ] `CACHE_INVALIDATION_SIGNALS is True`

## Error Handling
- [ ] Validate `ERROR_SETTINGS`
  - [ ] `ENABLE_DETAILED_ERRORS is True`
  - [ ] `ENABLE_ERROR_CODES is True`
  - [ ] `ENABLE_FIELD_ERRORS is True`
  - [ ] `ENABLE_VALIDATION_ERRORS is True`
  - [ ] `ENABLE_PERMISSION_ERRORS is True`
  - [ ] `ENABLE_AUTHENTICATION_ERRORS is True`
  - [ ] `ENABLE_RATE_LIMIT_ERRORS is True`
  - [ ] `ERROR_MESSAGE_LANGUAGE == 'en'`
  - [ ] `ENABLE_ERROR_LOGGING is True` and `LOG_LEVEL == 'ERROR'`

## File Uploads
- [ ] Validate `FILE_UPLOAD_SETTINGS`
  - [ ] `ENABLE_FILE_UPLOADS is True`
  - [ ] `MAX_FILE_SIZE == 10 * 1024 * 1024`
  - [ ] `MAX_FILES_PER_REQUEST == 10`
  - [ ] `ALLOWED_EXTENSIONS == ['.jpg','.jpeg','.png','.gif','.webp','.pdf','.txt','.csv','.json','.xml']`
  - [ ] `UPLOAD_PATH == 'uploads/'`
  - [ ] `ENABLE_VIRUS_SCANNING is False`
  - [ ] `ENABLE_IMAGE_PROCESSING is True` and `IMAGE_THUMBNAIL_SIZES == [(150,150),(300,300)]`
  - [ ] `ENABLE_FILE_VALIDATION is True`

## Monitoring and Health
- [ ] Validate `MONITORING_SETTINGS`
  - [ ] `ENABLE_METRICS is False`
  - [ ] `METRICS_BACKEND == 'prometheus'`
  - [ ] `ENABLE_QUERY_LOGGING is False`
  - [ ] `ENABLE_PERFORMANCE_LOGGING is False`
  - [ ] `ENABLE_ERROR_TRACKING is False` and `ERROR_TRACKING_DSN is None`
  - [ ] `ENABLE_HEALTH_CHECKS is True` and `HEALTH_CHECK_ENDPOINT == '/health/'`

## Extensions
- [ ] Validate `EXTENSION_SETTINGS`
  - [ ] `ENABLE_AUTH_EXTENSION is True`
  - [ ] `ENABLE_PERMISSION_EXTENSION is True`
  - [ ] `ENABLE_CACHING_EXTENSION is True`
  - [ ] `ENABLE_MONITORING_EXTENSION is False`
  - [ ] `ENABLE_FILE_EXTENSION is True`
  - [ ] `ENABLE_HEALTH_EXTENSION is True`

## Development
- [ ] Validate `DEVELOPMENT_SETTINGS`
  - [ ] `ENABLE_DEBUG_MODE is False`
  - [ ] `ENABLE_QUERY_PROFILING is False`
  - [ ] `ENABLE_SCHEMA_VALIDATION is True`
  - [ ] `ENABLE_TYPE_CHECKING is True`
  - [ ] `ENABLE_DEPRECATION_WARNINGS is True`
  - [ ] `ENABLE_PERFORMANCE_WARNINGS is True`

## Schema Registry
- [ ] Validate `SCHEMA_REGISTRY`
  - [ ] `ENABLE_AUTO_DISCOVERY is True`
  - [ ] `DISCOVERY_MODULES == ['models','schema','graphql']`
  - [ ] `ENABLE_SCHEMA_VALIDATION is True`
  - [ ] `ENABLE_SCHEMA_CACHING is True` and `SCHEMA_CACHE_TIMEOUT == 3600`

## Middleware
- [ ] Validate `MIDDLEWARE_SETTINGS`
  - [ ] `ENABLE_PERFORMANCE_MIDDLEWARE is True`
  - [ ] `ENABLE_AUTHENTICATION_MIDDLEWARE is True`
  - [ ] `ENABLE_PERMISSION_MIDDLEWARE is True`
  - [ ] `ENABLE_CACHING_MIDDLEWARE is False`
  - [ ] `ENABLE_RATE_LIMITING_MIDDLEWARE is False`
  - [ ] `ENABLE_CORS_MIDDLEWARE is True`
  - [ ] `ENABLE_ERROR_HANDLING_MIDDLEWARE is True`

## Internationalization (I18N)
- [ ] Validate `I18N_SETTINGS`
  - [ ] `ENABLE_I18N is False`
  - [ ] `DEFAULT_LANGUAGE == 'en'`
  - [ ] `SUPPORTED_LANGUAGES == ['en','fr','es','de']`
  - [ ] `ENABLE_FIELD_TRANSLATION is False`
  - [ ] `ENABLE_ERROR_TRANSLATION is True`

## Testing Settings
- [ ] Validate `TESTING_SETTINGS`
  - [ ] `ENABLE_TEST_MODE is False`
  - [ ] `ENABLE_MOCK_DATA is False`
  - [ ] `ENABLE_FIXTURES is True`
  - [ ] `ENABLE_FACTORY_BOY is True`
  - [ ] `ENABLE_COVERAGE is True` and `COVERAGE_THRESHOLD == 80`

## Configuration Validation
- [ ] Run `validate_configuration()` from `rail_django_graphql.conf` (should pass)
- [ ] Confirm required settings present: `DEFAULT_SCHEMA`, `ENABLE_GRAPHIQL`
- [ ] Verify types: `ENABLE_GRAPHIQL` (bool), `AUTHENTICATION_REQUIRED` (bool), `ENABLE_CACHING` (bool), `CACHE_TIMEOUT` (int), `DEFAULT_SCHEMA` (str), `SCHEMA_ENDPOINT` (str)
- [ ] Run `ConfigLoader.validate_configuration()` (should return `True`)

## Overrides
- [ ] Test Django override with `override_settings(RAIL_DJANGO_GRAPHQL={'ENABLE_GRAPHIQL': False})` and confirm proxy reads `False`
- [ ] Test schema-specific overrides using `get_settings_for_schema('admin')` then `set_schema_overrides({'ENABLE_GRAPHIQL': False})`
- [ ] Confirm global `settings.ENABLE_GRAPHIQL` remains `True`

## Integration Checks
- [ ] Attempt `ConfigLoader.load_schema_settings()` and confirm it returns a settings object (or skip if dependencies missing)
- [ ] Verify core/schema.py respects `SCHEMA_SETTINGS['excluded_apps']` (e.g., `getattr(self.settings, 'excluded_apps', [])` behavior)

## Utility Functions (defaults.py)
- [ ] `get_default_settings()` returns a dict containing keys like `DEFAULT_SCHEMA`, `ENABLE_GRAPHIQL`
- [ ] `get_schema_defaults('admin')` returns a dict with admin overrides
- [ ] `get_environment_defaults('development')` returns dict with debug enabled; `production` has debug disabled
- [ ] `merge_settings()` deep-merges nested dicts as expected

## Run Tests
- [ ] Optional: create `tests/test_library_defaults.py` and port the above checks to `unittest` or `pytest`
- [ ] Run `pytest -q` or `python manage.py test` and ensure all checks pass

Notes:
- These checks validate hierarchical resolution: schema overrides > Django overrides > library defaults.
- Some integration steps depend on optional components; skip or mark as informational if unavailable.