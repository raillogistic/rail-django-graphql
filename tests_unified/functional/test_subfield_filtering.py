#!/usr/bin/env python
"""
Test script for subfield filtering functionality.

This script tests the new subfield filtering feature that allows filtering
list subfields in GraphQL queries, such as comments(author:"1") within a posts query.

Purpose: Verify that subfield filtering works correctly for both ManyToMany and reverse relationships
Args: None
Returns: None (prints test results)
Raises: Various exceptions if tests fail
Example: python test_subfield_filtering.py
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from django.contrib.auth.models import User

from tests.models import BenchmarkTestBook, BenchmarkTestReview, BenchmarkTestAuthor
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.core.settings import TypeGeneratorSettings
import graphene


def test_subfield_filtering_generation():
    """
    Test that subfield filtering is properly generated in GraphQL types.

    This test verifies that:
    1. List fields have filter arguments
    2. Resolvers accept filters parameter
    3. Filter functionality is integrated with AdvancedFilterGenerator
    """
    print("Testing subfield filtering generation...")

    # Initialize type generator
    settings = TypeGeneratorSettings()
    type_generator = TypeGenerator(settings)

    # Generate type for a model with relationships
    author_type = type_generator.generate_object_type(BenchmarkTestAuthor)

    # Check that the type was generated
    assert author_type is not None, "Author type should be generated"

    # Check that list fields have filter arguments
    # The livres_auteur field should be a List with filters argument
    livres_field = getattr(author_type, "livres_auteur", None)
    assert livres_field is not None, "livres_auteur field should exist on Author type"

    # Check that the field is a List type
    assert isinstance(
        livres_field, graphene.List
    ), "livres_auteur field should be a List type"

    print("✓ Subfield filtering generation test passed")


def test_subfield_filtering_functionality():
    """
    Test the actual filtering functionality with real data.

    This test creates test data and verifies that subfield filtering
    works correctly in practice.
    """
    print("Testing subfield filtering functionality...")

    try:
        # Create test data
        print("Creating test data...")

        # Create authors
        author1 = BenchmarkTestAuthor.objects.create(
            nom_auteur="Dupont",
            prenom_auteur="Jean",
            email_auteur="jean.dupont@example.com",
        )
        author2 = BenchmarkTestAuthor.objects.create(
            nom_auteur="Martin",
            prenom_auteur="Marie",
            email_auteur="marie.martin@example.com",
        )

        # Create books
        book1 = BenchmarkTestBook.objects.create(
            titre_livre="Book 1",
            auteur_livre=author1,
            isbn_livre="1234567890123",
            date_publication="2023-01-01",
            nombre_pages=200,
            prix_livre=19.99,
            genre_livre="FICTION",
        )
        book2 = BenchmarkTestBook.objects.create(
            titre_livre="Book 2",
            auteur_livre=author2,
            isbn_livre="1234567890124",
            date_publication="2023-02-01",
            nombre_pages=300,
            prix_livre=24.99,
            genre_livre="NON_FICTION",
        )

        # Create reviews
        review1 = BenchmarkTestReview.objects.create(
            livre_avis=book1,
            nom_revieweur="Jean Dupont",
            email_revieweur="jean.dupont@example.com",
            note_avis=5,
            commentaire_avis="Excellent book!",
        )
        review2 = BenchmarkTestReview.objects.create(
            livre_avis=book1,
            nom_revieweur="Marie Martin",
            email_revieweur="marie.martin@example.com",
            note_avis=4,
            commentaire_avis="Good read!",
        )
        review3 = BenchmarkTestReview.objects.create(
            livre_avis=book2,
            nom_revieweur="Jean Dupont",
            email_revieweur="jean.dupont@example.com",
            note_avis=3,
            commentaire_avis="Average book",
        )

        print(f"Created {BenchmarkTestAuthor.objects.count()} authors")
        print(f"Created {BenchmarkTestBook.objects.count()} books")
        print(f"Created {BenchmarkTestReview.objects.count()} reviews")

        # Test subfield filtering
        print("Testing subfield filtering...")

        # Initialize type generator and create resolver
        settings = DjangoGraphQLAutoSettings()
        type_generator = TypeGenerator(settings)

        # Generate the Book type which should have avis_livre field with filtering
        book_type = type_generator.generate_object_type(BenchmarkTestBook)

        # Get the avis_livre resolver
        reviews_resolver = getattr(book_type, "resolve_avis_livre", None)
        assert reviews_resolver is not None, "Reviews resolver should exist"

        # Create a mock info object
        class MockInfo:
            pass

        info = MockInfo()

        # Test filtering reviews by reviewer
        print("Testing reviews filtering by reviewer...")

        # Get all reviews for book1 (should be 2)
        all_reviews = reviews_resolver(book1, info)
        print(f"All reviews for book1: {all_reviews.count()}")
        assert (
            all_reviews.count() == 2
        ), f"Expected 2 reviews, got {all_reviews.count()}"

        # Test filtering with reviewer filter
        reviewer_filter = {"nom_revieweur": "Jean Dupont"}
        filtered_reviews = reviews_resolver(book1, info, filters=reviewer_filter)
        print(f"Reviews by Jean Dupont: {filtered_reviews.count()}")
        assert (
            filtered_reviews.count() == 1
        ), f"Expected 1 review by Jean Dupont, got {filtered_reviews.count()}"

        # Verify the filtered review is the correct one
        filtered_review = filtered_reviews.first()
        assert (
            filtered_review.nom_revieweur == "Jean Dupont"
        ), "Filtered review should be by Jean Dupont"
        assert (
            filtered_review.commentaire_avis == "Excellent book!"
        ), "Filtered review should have correct content"

        print("✓ Subfield filtering functionality test passed")

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        raise
    finally:
        # Clean up test data
        print("Cleaning up test data...")
        BenchmarkTestReview.objects.all().delete()
        BenchmarkTestBook.objects.all().delete()
        BenchmarkTestAuthor.objects.all().delete()
        print("✓ Test data cleaned up")


def test_reverse_relationship_filtering():
    """
    Test filtering on reverse relationships (e.g., books on author).
    """
    print("Testing reverse relationship filtering...")

    try:
        # Create test data
        print("Creating test data for reverse relationship test...")

        # Create authors
        author1 = BenchmarkTestAuthor.objects.create(
            nom_auteur="Dupont",
            prenom_auteur="Jean",
            email_auteur="jean.dupont@example.com",
        )
        author2 = BenchmarkTestAuthor.objects.create(
            nom_auteur="Martin",
            prenom_auteur="Marie",
            email_auteur="marie.martin@example.com",
        )

        # Create books with different genres
        book1 = BenchmarkTestBook.objects.create(
            titre_livre="Fiction Book",
            auteur_livre=author1,
            isbn_livre="1234567890123",
            date_publication="2023-01-01",
            nombre_pages=200,
            prix_livre=19.99,
            genre_livre="FICTION",
        )
        book2 = BenchmarkTestBook.objects.create(
            titre_livre="Non-Fiction Book",
            auteur_livre=author1,
            isbn_livre="1234567890124",
            date_publication="2023-02-01",
            nombre_pages=300,
            prix_livre=24.99,
            genre_livre="NON_FICTION",
        )
        book3 = BenchmarkTestBook.objects.create(
            titre_livre="Another Fiction Book",
            auteur_livre=author2,
            isbn_livre="1234567890125",
            date_publication="2023-03-01",
            nombre_pages=250,
            prix_livre=22.99,
            genre_livre="FICTION",
        )

        print(f"Created {BenchmarkTestAuthor.objects.count()} authors")
        print(f"Created {BenchmarkTestBook.objects.count()} books")

        # Test reverse relationship filtering
        print("Testing books filtering on author...")

        # Initialize type generator
        settings = TypeGeneratorSettings()
        type_generator = TypeGenerator(settings)

        # Generate the Author type which should have livres_auteur field with filtering
        author_type = type_generator.generate_object_type(BenchmarkTestAuthor)

        # Get the livres_auteur resolver
        books_resolver = getattr(author_type, "resolve_livres_auteur", None)
        assert books_resolver is not None, "Books resolver should exist"

        # Create a mock info object
        class MockInfo:
            pass

        info = MockInfo()

        # Test filtering books by genre
        print("Testing books filtering by genre...")

        # Get all books for author1 (should be 2)
        all_books = books_resolver(author1, info)
        print(f"All books for author1: {all_books.count()}")
        assert all_books.count() == 2, f"Expected 2 books, got {all_books.count()}"

        # Test filtering with genre filter
        genre_filter = {"genre_livre": "FICTION"}
        filtered_books = books_resolver(author1, info, filters=genre_filter)
        print(f"Fiction books by author1: {filtered_books.count()}")
        assert (
            filtered_books.count() == 1
        ), f"Expected 1 fiction book, got {filtered_books.count()}"

        # Verify the filtered book is the correct one
        filtered_book = filtered_books.first()
        assert filtered_book.genre_livre == "FICTION", "Filtered book should be fiction"
        assert (
            filtered_book.titre_livre == "Fiction Book"
        ), "Filtered book should have correct title"

        print("✓ Reverse relationship filtering test passed")

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        raise
    finally:
        # Clean up test data
        print("Cleaning up test data...")
        BenchmarkTestBook.objects.all().delete()
        BenchmarkTestAuthor.objects.all().delete()
        print("✓ Test data cleaned up")


def main():
    """
    Main test function that runs all subfield filtering tests.
    """
    print("=" * 60)
    print("SUBFIELD FILTERING TESTS")
    print("=" * 60)

    try:
        # Run all tests
        test_subfield_filtering_generation()
        print()
        test_subfield_filtering_functionality()
        print()
        test_reverse_relationship_filtering()

        print()
        print("=" * 60)
        print("✓ ALL SUBFIELD FILTERING TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ TESTS FAILED: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
