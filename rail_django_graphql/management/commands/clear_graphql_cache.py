"""
Management command to clear GraphQL-related caches.

This command is intended for development and troubleshooting. In production,
use with caution as it may clear shared cache entries.

Usage:
    python manage.py clear_graphql_cache

Options:
    --all: Clear the entire cache backend (dangerous in shared environments)

"""

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.core.cache import cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Clear GraphQL caches (query results, metadata)."""

    help = "Clear GraphQL-related caches to avoid stale data during development."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clear the entire cache backend (use with caution)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        clear_all = options.get("all", False)

        if clear_all:
            cache.clear()
            self.stdout.write(self.style.WARNING("Entire cache backend cleared."))
            logger.warning("Entire cache backend cleared via clear_graphql_cache command.")
            return

        # Best-effort invalidation: clear known GraphQL cache entries by prefixes if supported
        # Note: Most Django cache backends do not support iterating keys. As a fallback, we clear
        # the entire cache. In DEBUG mode, middleware and query caching are disabled, so stale
        # entries are ignored, but this command helps when caches were previously enabled.
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("GraphQL caches cleared (global)."))
            logger.info("GraphQL caches cleared (global) via management command.")
        except Exception as exc:
            logger.error(f"Failed to clear cache: {exc}")
            self.stderr.write(self.style.ERROR(f"Failed to clear cache: {exc}"))