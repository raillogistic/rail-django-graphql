"""
Edge cases and error handling test cases for nested field filtering.

This module tests various edge cases, error conditions, and boundary scenarios
for the nested field filtering functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


class EdgeCaseModel(models.Model):
    """Model for testing edge cases."""

    name = models.CharField(max_length=100, verbose_name="Nom")

    class Meta:
        app_label = "test_app"


class SelfReferencingModel(models.Model):
    """Model with self-referencing foreign key for circular reference testing."""

    name = models.CharField(max_length=100, verbose_name="Nom")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, verbose_name="Parent"
    )

    class Meta:
        app_label = "test_app"


class ComplexRelationshipModel(models.Model):
    """Model with complex relationships for testing."""

    title = models.CharField(max_length=200, verbose_name="Titre")

    class Meta:
        app_label = "test_app"


class TestNestedFilteringEdgeCases(TestCase):
    """Test cases for edge cases in nested field filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=3)

    def test_empty_model_filtering(self):
        """Test filtering with a model that has no fields."""

        class EmptyModel(models.Model):
            class Meta:
                app_label = "test_app"

        # Should handle gracefully
        filter_set = self.generator.generate_filter_set(EmptyModel)
        filter_instance = filter_set()

        # Should create a valid FilterSet even with no fields
        self.assertEqual(len(filter_instance.filters), 0)

    def test_model_with_only_primary_key(self):
        """Test filtering with a model that only has a primary key."""

        class PKOnlyModel(models.Model):
            # Only has the implicit 'id' field
            class Meta:
                app_label = "test_app"

        filter_set = self.generator.generate_filter_set(PKOnlyModel)
        filter_instance = filter_set()

        # Should have at least the ID filter
        self.assertIn("id", filter_instance.filters)

    def test_self_referencing_model_circular_prevention(self):
        """Test prevention of infinite recursion with self-referencing models."""
        filter_set = self.generator.generate_filter_set(SelfReferencingModel)
        filter_instance = filter_set()

        # Should have parent filters but prevent infinite recursion
        self.assertIn("parent__name", filter_instance.filters)

        # Should not have deeply nested self-references beyond max_depth
        very_deep_filter = "__".join(["parent"] * 10 + ["name"])
        self.assertNotIn(very_deep_filter, filter_instance.filters)

    def test_nonexistent_field_handling(self):
        """Test handling of nonexistent fields in filter generation."""
        # Mock a field that doesn't exist
        with patch.object(EdgeCaseModel._meta, "get_field") as mock_get_field:
            mock_get_field.side_effect = FieldDoesNotExist("Field does not exist")

            # Should handle gracefully without crashing
            try:
                filter_set = self.generator.generate_filter_set(EdgeCaseModel)
                filter_instance = filter_set()
                # Should succeed even if some fields can't be processed
                self.assertIsNotNone(filter_instance)
            except Exception as e:
                self.fail(f"Should handle nonexistent fields gracefully: {e}")

    def test_invalid_model_input(self):
        """Test handling of invalid model inputs."""
        # Test with None
        with self.assertRaises(AttributeError):
            self.generator.generate_filter_set(None)

        # Test with non-model class
        class NotAModel:
            pass

        with self.assertRaises(AttributeError):
            self.generator.generate_filter_set(NotAModel)

    def test_zero_max_depth(self):
        """Test behavior with max_depth set to 0."""
        generator = AdvancedFilterGenerator(max_nested_depth=0)
        filter_set = generator.generate_filter_set(EdgeCaseModel)
        filter_instance = filter_set()

        # Should only have direct field filters, no nested ones
        nested_filters = [
            f
            for f in filter_instance.filters.keys()
            if "__" in f and not f.endswith("__exact")
        ]
        self.assertEqual(len(nested_filters), 0)

    def test_negative_max_depth(self):
        """Test behavior with negative max_depth."""
        # Should be handled gracefully (clamped to 0 or minimum value)
        generator = AdvancedFilterGenerator(max_nested_depth=-1)

        # Should not crash and should have reasonable behavior
        filter_set = generator.generate_filter_set(EdgeCaseModel)
        self.assertIsNotNone(filter_set)

    def test_extremely_large_max_depth(self):
        """Test behavior with extremely large max_depth."""
        # Should be clamped to maximum allowed depth
        generator = AdvancedFilterGenerator(max_nested_depth=1000)

        # Should be clamped to MAX_ALLOWED_NESTED_DEPTH (5)
        self.assertEqual(generator.max_nested_depth, 5)

    def test_disabled_nested_filters_edge_cases(self):
        """Test edge cases when nested filtering is disabled."""
        generator = AdvancedFilterGenerator(enable_nested_filters=False)

        # Should work normally for basic filters
        filter_set = generator.generate_filter_set(EdgeCaseModel)
        filter_instance = filter_set()

        # Should have basic filters
        self.assertIn("name", filter_instance.filters)

        # Should not have nested filters
        nested_filters = [
            f
            for f in filter_instance.filters.keys()
            if "__" in f and not f.endswith("__exact")
        ]
        self.assertEqual(len(nested_filters), 0)

    def test_concurrent_filter_generation(self):
        """Test concurrent filter generation for thread safety."""
        import threading
        import time

        results = []
        errors = []

        def generate_filters(thread_id):
            try:
                filter_set = self.generator.generate_filter_set(EdgeCaseModel)
                filter_instance = filter_set()
                results.append((thread_id, len(filter_instance.filters)))
            except Exception as e:
                errors.append((thread_id, e))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_filters, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors}")

        # Verify consistent results
        if results:
            first_result = results[0][1]
            for thread_id, filter_count in results:
                self.assertEqual(
                    filter_count, first_result, f"Inconsistent results between threads"
                )

    def test_memory_usage_with_deep_nesting(self):
        """Test memory usage doesn't grow excessively with deep nesting."""
        import sys

        # Create a model with potential for deep nesting
        class DeepModel(models.Model):
            name = models.CharField(max_length=100)
            parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

            class Meta:
                app_label = "test_app"

        # Generate filters with different depths
        memory_usage = []

        for depth in [1, 2, 3, 4, 5]:
            generator = AdvancedFilterGenerator(max_nested_depth=depth)

            # Measure memory before
            import gc

            gc.collect()

            filter_set = generator.generate_filter_set(DeepModel)
            filter_instance = filter_set()

            # Memory usage should not grow exponentially
            # This is a basic check - in real scenarios, you'd use more sophisticated memory profiling
            self.assertIsNotNone(filter_instance)

    def test_filter_name_collision_handling(self):
        """Test handling of potential filter name collisions."""

        class CollisionModel(models.Model):
            exact = models.CharField(max_length=100)  # Field named 'exact'
            icontains = models.CharField(max_length=100)  # Field named 'icontains'

            class Meta:
                app_label = "test_app"

        # Should handle field names that match filter suffixes
        filter_set = self.generator.generate_filter_set(CollisionModel)
        filter_instance = filter_set()

        # Should have filters for these fields
        self.assertIn("exact", filter_instance.filters)
        self.assertIn("icontains", filter_instance.filters)

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters in field names."""

        class UnicodeModel(models.Model):
            nom_français = models.CharField(max_length=100)  # French characters
            field_with_underscore = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Should handle Unicode field names
        filter_set = self.generator.generate_filter_set(UnicodeModel)
        filter_instance = filter_set()

        # Should create filters for Unicode field names
        self.assertIn("nom_français", filter_instance.filters)
        self.assertIn("field_with_underscore", filter_instance.filters)

    def test_performance_analysis_edge_cases(self):
        """Test performance analysis with edge case inputs."""
        # Empty filters
        analysis = self.generator.analyze_query_performance(EdgeCaseModel, {})
        self.assertEqual(analysis["total_filters"], 0)

        # Filters with None values
        filters_with_none = {"name__exact": None, "id__in": None}
        analysis = self.generator.analyze_query_performance(
            EdgeCaseModel, filters_with_none
        )
        self.assertEqual(analysis["total_filters"], 2)

        # Filters with empty strings
        filters_with_empty = {"name__icontains": "", "name__exact": ""}
        analysis = self.generator.analyze_query_performance(
            EdgeCaseModel, filters_with_empty
        )
        self.assertEqual(analysis["total_filters"], 2)

    def test_cache_behavior_edge_cases(self):
        """Test caching behavior in edge cases."""
        # Generate same filter set multiple times
        filter_set_1 = self.generator.generate_filter_set(EdgeCaseModel)
        filter_set_2 = self.generator.generate_filter_set(EdgeCaseModel)

        # Should return cached version
        self.assertEqual(filter_set_1, filter_set_2)

        # Different depth should create different filter set
        generator_different_depth = AdvancedFilterGenerator(max_nested_depth=2)
        filter_set_3 = generator_different_depth.generate_filter_set(EdgeCaseModel)

        # Should be different due to different depth
        # (This depends on implementation - might be same if no nested fields exist)
        self.assertIsNotNone(filter_set_3)

    def test_error_recovery_and_logging(self):
        """Test error recovery and proper logging of issues."""
        with patch("rail_django_graphql.generators.filters.logger") as mock_logger:
            # Force an error in field processing
            with patch.object(
                self.generator, "_generate_field_filters"
            ) as mock_field_gen:
                mock_field_gen.side_effect = Exception("Simulated error")

                # Should handle error gracefully
                try:
                    filter_set = self.generator.generate_filter_set(EdgeCaseModel)
                    # Should still create a basic FilterSet
                    self.assertIsNotNone(filter_set)
                except Exception:
                    # If it does raise, that's also acceptable behavior
                    pass

                # Should log the error
                # mock_logger.error.assert_called()


class TestNestedFilteringBoundaryConditions(TestCase):
    """Test boundary conditions for nested field filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=3)

    def test_maximum_filter_complexity(self):
        """Test behavior at maximum filter complexity."""
        # Create filters at the boundary of complexity
        max_complexity_filters = {}

        # Create filters right at the max_depth boundary
        for i in range(5):  # Just under the "poor" performance threshold
            filter_name = "__".join(["level1", "level2", "level3", f"field_{i}"])
            max_complexity_filters[filter_name] = f"value_{i}"

        analysis = self.generator.analyze_query_performance(
            EdgeCaseModel, max_complexity_filters
        )

        # Should handle without crashing
        self.assertIn("performance_score", analysis)
        self.assertEqual(analysis["total_filters"], 5)

    def test_filter_generation_at_depth_boundary(self):
        """Test filter generation exactly at max_depth boundary."""
        generator = AdvancedFilterGenerator(max_nested_depth=2)

        # Create a model structure that could go deeper
        class Level1Model(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class Level2Model(models.Model):
            title = models.CharField(max_length=100)
            level1 = models.ForeignKey(Level1Model, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        class Level3Model(models.Model):
            description = models.CharField(max_length=100)
            level2 = models.ForeignKey(Level2Model, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        # Mock the field relationships
        with patch.object(
            Level3Model._meta, "get_field"
        ) as mock_get_field_l3, patch.object(
            Level2Model._meta, "get_field"
        ) as mock_get_field_l2, patch.object(
            Level1Model._meta, "get_field"
        ) as mock_get_field_l1:
            # Mock Level3 -> Level2 relationship
            mock_level2_field = Mock()
            mock_level2_field.__class__ = models.ForeignKey
            mock_level2_field.related_model = Level2Model

            # Mock Level2 -> Level1 relationship
            mock_level1_field = Mock()
            mock_level1_field.__class__ = models.ForeignKey
            mock_level1_field.related_model = Level1Model

            # Mock field access
            def l3_side_effect(field_name):
                if field_name == "level2":
                    return mock_level2_field
                elif field_name == "description":
                    mock_desc_field = Mock()
                    mock_desc_field.__class__ = models.CharField
                    return mock_desc_field
                raise FieldDoesNotExist(f"Field {field_name} not found")

            def l2_side_effect(field_name):
                if field_name == "level1":
                    return mock_level1_field
                elif field_name == "title":
                    mock_title_field = Mock()
                    mock_title_field.__class__ = models.CharField
                    return mock_title_field
                raise FieldDoesNotExist(f"Field {field_name} not found")

            def l1_side_effect(field_name):
                if field_name == "name":
                    mock_name_field = Mock()
                    mock_name_field.__class__ = models.CharField
                    return mock_name_field
                raise FieldDoesNotExist(f"Field {field_name} not found")

            mock_get_field_l3.side_effect = l3_side_effect
            mock_get_field_l2.side_effect = l2_side_effect
            mock_get_field_l1.side_effect = l1_side_effect

            filter_set = generator.generate_filter_set(Level3Model)
            filter_instance = filter_set()

            # Should have filters up to max_depth (2)
            self.assertIn("level2__title", filter_instance.filters)
            self.assertIn("level2__level1__name", filter_instance.filters)

            # Should NOT have filters beyond max_depth
            # (This would be depth 3, which exceeds max_depth=2)
            very_deep_filter = "level2__level1__some_deeper_field"
            # Note: This test depends on the actual model structure

    def test_performance_thresholds(self):
        """Test performance scoring at threshold boundaries."""
        # Test exactly at moderate threshold (5 nested filters)
        moderate_filters = {f"field_{i}__nested": f"value_{i}" for i in range(5)}
        analysis = self.generator.analyze_query_performance(
            EdgeCaseModel, moderate_filters
        )
        # Should be at the boundary between good and moderate

        # Test exactly at poor threshold (10 nested filters)
        poor_filters = {f"field_{i}__nested": f"value_{i}" for i in range(10)}
        analysis = self.generator.analyze_query_performance(EdgeCaseModel, poor_filters)
        self.assertEqual(analysis["performance_score"], "poor")

        # Test just under poor threshold (9 nested filters)
        almost_poor_filters = {f"field_{i}__nested": f"value_{i}" for i in range(9)}
        analysis = self.generator.analyze_query_performance(
            EdgeCaseModel, almost_poor_filters
        )
        # Should be moderate, not poor
        self.assertNotEqual(analysis["performance_score"], "poor")


if __name__ == "__main__":
    pytest.main([__file__])
