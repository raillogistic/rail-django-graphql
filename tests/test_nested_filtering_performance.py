"""
Performance optimization test cases for nested field filtering.

This module specifically tests the performance analysis and optimization
features of the AdvancedFilterGenerator for nested field filtering.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.db.models import QuerySet
from rail_django_graphql.generators.filters import AdvancedFilterGenerator


class MockModel(models.Model):
    """Mock model for performance testing."""

    name = models.CharField(max_length=100, verbose_name="Nom")

    class Meta:
        app_label = "test_app"


class MockRelatedModel(models.Model):
    """Mock related model for performance testing."""

    title = models.CharField(max_length=100, verbose_name="Titre")
    parent = models.ForeignKey(
        MockModel, on_delete=models.CASCADE, verbose_name="Parent"
    )

    class Meta:
        app_label = "test_app"


class MockDeeplyNestedModel(models.Model):
    """Mock deeply nested model for performance testing."""

    description = models.TextField(verbose_name="Description")
    related = models.ForeignKey(
        MockRelatedModel, on_delete=models.CASCADE, verbose_name="Lié"
    )

    class Meta:
        app_label = "test_app"


class TestNestedFilteringPerformanceAnalysis(TestCase):
    """Test cases for performance analysis functionality in nested filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=4)

    def test_simple_filter_performance_analysis(self):
        """Test performance analysis for simple filters."""
        simple_filters = {"name__icontains": "test", "name__exact": "specific"}

        analysis = self.generator.analyze_query_performance(MockModel, simple_filters)

        # Should have good performance score for simple filters
        self.assertEqual(analysis["performance_score"], "good")
        self.assertEqual(analysis["nested_filters"], 0)
        self.assertEqual(analysis["max_depth"], 0)
        self.assertEqual(len(analysis["select_related_suggestions"]), 0)
        self.assertEqual(len(analysis["prefetch_related_suggestions"]), 0)

    def test_moderate_complexity_filter_analysis(self):
        """Test performance analysis for moderately complex filters."""
        moderate_filters = {
            "name__icontains": "test",
            "related__title__exact": "specific",
            "related__parent__name__icontains": "parent",
            "field1__nested": "value1",
            "field2__nested": "value2",
            "field3__nested": "value3",
        }

        analysis = self.generator.analyze_query_performance(
            MockDeeplyNestedModel, moderate_filters
        )

        # Should have moderate performance score
        self.assertEqual(analysis["performance_score"], "moderate")
        self.assertGreater(analysis["nested_filters"], 3)
        self.assertGreater(analysis["max_depth"], 1)

    def test_complex_filter_performance_analysis(self):
        """Test performance analysis for complex filters."""
        complex_filters = {}

        # Create many nested filters
        for i in range(15):
            complex_filters[f"field_{i}__nested__deep__value"] = f"value_{i}"

        analysis = self.generator.analyze_query_performance(MockModel, complex_filters)

        # Should have poor performance score
        self.assertEqual(analysis["performance_score"], "poor")
        self.assertEqual(analysis["nested_filters"], 15)
        self.assertGreater(analysis["max_depth"], 3)

    def test_depth_calculation_accuracy(self):
        """Test accurate depth calculation for nested filters."""
        test_cases = [
            ("field__exact", 0),  # No nesting (exact is lookup)
            ("field__nested__exact", 1),  # One level of nesting
            ("field__nested__deep__exact", 2),  # Two levels of nesting
            ("field__very__deeply__nested__exact", 3),  # Three levels of nesting
        ]

        for filter_name, expected_depth in test_cases:
            filters = {filter_name: "test_value"}
            analysis = self.generator.analyze_query_performance(MockModel, filters)
            self.assertEqual(
                analysis["max_depth"],
                expected_depth,
                f"Failed for filter: {filter_name}",
            )

    def test_select_related_suggestions(self):
        """Test generation of select_related optimization suggestions."""
        filters_with_foreign_keys = {
            "related__title__icontains": "test",
            "related__parent__name__exact": "parent",
            "another_fk__field__value": "test",
        }

        # Mock the model fields to simulate ForeignKey relationships
        with patch.object(MockDeeplyNestedModel._meta, "get_field") as mock_get_field:
            # Mock related field as ForeignKey
            mock_related_field = Mock()
            mock_related_field.__class__ = models.ForeignKey
            mock_related_field.related_model = MockRelatedModel

            # Mock parent field as ForeignKey
            mock_parent_field = Mock()
            mock_parent_field.__class__ = models.ForeignKey
            mock_parent_field.related_model = MockModel

            def side_effect(field_name):
                if field_name == "related":
                    return mock_related_field
                elif field_name == "parent":
                    return mock_parent_field
                else:
                    raise Exception(f"Field {field_name} not found")

            mock_get_field.side_effect = side_effect

            analysis = self.generator.analyze_query_performance(
                MockDeeplyNestedModel, filters_with_foreign_keys
            )

            # Should suggest select_related optimizations
            self.assertGreater(len(analysis["select_related_suggestions"]), 0)
            self.assertIn("related", analysis["select_related_suggestions"])

    def test_prefetch_related_suggestions(self):
        """Test generation of prefetch_related optimization suggestions."""
        # This would typically be for reverse relationships or ManyToMany
        filters_with_reverse_relations = {
            "reverse_relation__field__value": "test",
            "many_to_many__field__value": "test",
        }

        # Mock reverse relationship fields
        with patch.object(MockModel._meta, "get_field") as mock_get_field:
            mock_reverse_field = Mock()
            mock_reverse_field.related_model = MockRelatedModel
            # Simulate a reverse relationship (not ForeignKey or OneToOneField)
            mock_reverse_field.__class__ = models.ManyToManyField

            def side_effect(field_name):
                if field_name in ["reverse_relation", "many_to_many"]:
                    return mock_reverse_field
                else:
                    raise Exception(f"Field {field_name} not found")

            mock_get_field.side_effect = side_effect

            analysis = self.generator.analyze_query_performance(
                MockModel, filters_with_reverse_relations
            )

            # Should suggest prefetch_related optimizations
            self.assertGreater(len(analysis["prefetch_related_suggestions"]), 0)

    def test_n_plus_one_risk_detection(self):
        """Test detection of potential N+1 query risks."""
        risky_filters = {
            "reverse_items__field__value": "test",
            "many_to_many_field__nested__value": "test",
        }

        with patch.object(MockModel._meta, "get_field") as mock_get_field:
            mock_risky_field = Mock()
            mock_risky_field.related_model = MockRelatedModel
            mock_risky_field.__class__ = models.ManyToManyField

            mock_get_field.return_value = mock_risky_field

            analysis = self.generator.analyze_query_performance(
                MockModel, risky_filters
            )

            # Should detect N+1 risks
            self.assertGreater(len(analysis["potential_n_plus_one_risks"]), 0)

    def test_recommendation_generation(self):
        """Test generation of performance recommendations."""
        complex_filters = {
            "related__title__icontains": "test",
            "related__parent__name__exact": "parent",
        }

        with patch.object(MockDeeplyNestedModel._meta, "get_field") as mock_get_field:
            mock_related_field = Mock()
            mock_related_field.__class__ = models.ForeignKey
            mock_related_field.related_model = MockRelatedModel

            mock_parent_field = Mock()
            mock_parent_field.__class__ = models.ForeignKey
            mock_parent_field.related_model = MockModel

            def side_effect(field_name):
                if field_name == "related":
                    return mock_related_field
                elif field_name == "parent":
                    return mock_parent_field
                else:
                    raise Exception(f"Field {field_name} not found")

            mock_get_field.side_effect = side_effect

            analysis = self.generator.analyze_query_performance(
                MockDeeplyNestedModel, complex_filters
            )

            # Should generate recommendations
            self.assertGreater(len(analysis["recommendations"]), 0)

            # Check for specific recommendation types
            recommendations_text = " ".join(analysis["recommendations"])
            self.assertIn("select_related", recommendations_text)


class TestNestedFilteringQuerySetOptimization(TestCase):
    """Test cases for QuerySet optimization functionality in nested filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=3)

    @patch("rail_django_graphql.generators.filters.logger")
    def test_get_optimized_queryset_with_select_related(self, mock_logger):
        """Test QuerySet optimization with select_related."""
        filters = {
            "related__title__icontains": "test",
            "related__parent__name__exact": "parent",
        }

        # Mock QuerySet
        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset

        # Mock model.objects.all()
        with patch.object(
            MockDeeplyNestedModel.objects, "all", return_value=mock_queryset
        ):
            # Mock the performance analysis to return select_related suggestions
            with patch.object(
                self.generator, "analyze_query_performance"
            ) as mock_analysis:
                mock_analysis.return_value = {
                    "select_related_suggestions": ["related", "related__parent"],
                    "prefetch_related_suggestions": [],
                }

                optimized_qs = self.generator.get_optimized_queryset(
                    MockDeeplyNestedModel, filters
                )

                # Verify select_related was called
                mock_queryset.select_related.assert_called_once_with(
                    "related", "related__parent"
                )

                # Verify logging
                mock_logger.debug.assert_called()

    @patch("rail_django_graphql.generators.filters.logger")
    def test_get_optimized_queryset_with_prefetch_related(self, mock_logger):
        """Test QuerySet optimization with prefetch_related."""
        filters = {"reverse_items__field__value": "test"}

        # Mock QuerySet
        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset

        with patch.object(MockModel.objects, "all", return_value=mock_queryset):
            with patch.object(
                self.generator, "analyze_query_performance"
            ) as mock_analysis:
                mock_analysis.return_value = {
                    "select_related_suggestions": [],
                    "prefetch_related_suggestions": ["reverse_items"],
                }

                optimized_qs = self.generator.get_optimized_queryset(MockModel, filters)

                # Verify prefetch_related was called
                mock_queryset.prefetch_related.assert_called_once_with("reverse_items")

                # Verify logging
                mock_logger.debug.assert_called()

    def test_get_optimized_queryset_with_base_queryset(self):
        """Test QuerySet optimization with a provided base queryset."""
        filters = {"name__icontains": "test"}

        # Create a base queryset
        base_queryset = Mock(spec=QuerySet)
        base_queryset.select_related.return_value = base_queryset
        base_queryset.prefetch_related.return_value = base_queryset

        with patch.object(self.generator, "analyze_query_performance") as mock_analysis:
            mock_analysis.return_value = {
                "select_related_suggestions": [],
                "prefetch_related_suggestions": [],
            }

            optimized_qs = self.generator.get_optimized_queryset(
                MockModel, filters, base_queryset=base_queryset
            )

            # Should use the provided base queryset
            self.assertEqual(optimized_qs, base_queryset)

    def test_optimization_with_no_suggestions(self):
        """Test QuerySet optimization when no optimizations are suggested."""
        filters = {"name__exact": "test"}

        mock_queryset = Mock(spec=QuerySet)

        with patch.object(MockModel.objects, "all", return_value=mock_queryset):
            with patch.object(
                self.generator, "analyze_query_performance"
            ) as mock_analysis:
                mock_analysis.return_value = {
                    "select_related_suggestions": [],
                    "prefetch_related_suggestions": [],
                }

                optimized_qs = self.generator.get_optimized_queryset(MockModel, filters)

                # Should return the original queryset without modifications
                self.assertEqual(optimized_qs, mock_queryset)

                # Verify optimization methods were not called
                mock_queryset.select_related.assert_not_called()
                mock_queryset.prefetch_related.assert_not_called()


class TestNestedFilteringPerformanceEdgeCases(TestCase):
    """Test edge cases in nested filtering performance optimization."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=2)

    def test_empty_filters_performance_analysis(self):
        """Test performance analysis with empty filters."""
        analysis = self.generator.analyze_query_performance(MockModel, {})

        self.assertEqual(analysis["total_filters"], 0)
        self.assertEqual(analysis["nested_filters"], 0)
        self.assertEqual(analysis["max_depth"], 0)
        self.assertEqual(analysis["performance_score"], "good")
        self.assertEqual(len(analysis["recommendations"]), 0)

    def test_invalid_filter_names_handling(self):
        """Test handling of invalid filter names in performance analysis."""
        invalid_filters = {
            "nonexistent_field__value": "test",
            "invalid__nested__field": "test",
        }

        # Should handle gracefully without crashing
        analysis = self.generator.analyze_query_performance(MockModel, invalid_filters)

        # Should still provide basic analysis
        self.assertEqual(analysis["total_filters"], 2)
        self.assertEqual(analysis["nested_filters"], 2)

    def test_very_deep_nesting_performance_impact(self):
        """Test performance analysis with very deep nesting."""
        very_deep_filters = {
            "level1__level2__level3__level4__level5__level6__value": "test"
        }

        analysis = self.generator.analyze_query_performance(
            MockModel, very_deep_filters
        )

        # Should detect poor performance
        self.assertEqual(analysis["performance_score"], "poor")
        self.assertEqual(analysis["max_depth"], 6)

        # Should recommend reducing depth
        recommendations_text = " ".join(analysis["recommendations"])
        self.assertIn("reducing max_nested_depth", recommendations_text)

    def test_performance_analysis_serialization(self):
        """Test that performance analysis results are JSON serializable."""
        import json

        filters = {"related__field__value": "test", "another__nested__field": "test"}

        analysis = self.generator.analyze_query_performance(MockModel, filters)

        # Should be JSON serializable
        try:
            json_str = json.dumps(analysis)
            reconstructed = json.loads(json_str)
            self.assertEqual(analysis["model"], reconstructed["model"])
            self.assertEqual(analysis["total_filters"], reconstructed["total_filters"])
        except (TypeError, ValueError) as e:
            self.fail(f"Performance analysis result is not JSON serializable: {e}")

    def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring systems."""
        filters = {
            "category__name__icontains": "electronics",
            "brand__country__name__exact": "USA",
            "price__gte": 100,
        }

        # Mock performance monitoring
        with patch("rail_django_graphql.generators.filters.logger") as mock_logger:
            analysis = self.generator.analyze_query_performance(MockModel, filters)

            # Verify performance metrics are logged
            mock_logger.info.assert_called()

            # Check log message contains performance information
            log_calls = mock_logger.info.call_args_list
            performance_logged = any(
                "Performance analysis" in str(call) for call in log_calls
            )
            self.assertTrue(performance_logged)

    def test_concurrent_filter_analysis(self):
        """Test performance analysis under concurrent access scenarios."""
        import threading
        import time

        results = []
        errors = []

        def analyze_filters(thread_id):
            try:
                filters = {f"field_{thread_id}__nested__value": f"test_{thread_id}"}
                analysis = self.generator.analyze_query_performance(MockModel, filters)
                results.append((thread_id, analysis))
            except Exception as e:
                errors.append((thread_id, e))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_filters, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify all analyses completed
        self.assertEqual(len(results), 5)

        # Verify each analysis is valid
        for thread_id, analysis in results:
            self.assertIn("model", analysis)
            self.assertIn("performance_score", analysis)
            self.assertEqual(analysis["total_filters"], 1)


if __name__ == "__main__":
    pytest.main([__file__])
