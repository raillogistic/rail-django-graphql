# Guide d'Écriture de Tests - Django GraphQL Auto

Ce guide fournit des directives détaillées pour écrire des tests efficaces et maintenables pour le projet Django GraphQL Auto.

## 📋 Table des Matières

- [Principes Fondamentaux](#principes-fondamentaux)
- [Structure des Tests](#structure-des-tests)
- [Patterns de Test](#patterns-de-test)
- [Tests par Composant](#tests-par-composant)
- [Gestion des Données](#gestion-des-données)
- [Assertions et Validations](#assertions-et-validations)
- [Performance et Optimisation](#performance-et-optimisation)
- [Exemples Pratiques](#exemples-pratiques)

## 🎯 Principes Fondamentaux

### 1. Tests FIRST

- **Fast** : Rapides à exécuter
- **Independent** : Indépendants les uns des autres
- **Repeatable** : Reproductibles dans tout environnement
- **Self-Validating** : Résultat binaire (succès/échec)
- **Timely** : Écrits au bon moment

### 2. Structure AAA (Arrange, Act, Assert)

```python
def test_model_introspector_analyzes_simple_model():
    """Test d'analyse d'un modèle simple par ModelIntrospector."""

    # Arrange - Préparation des données et du contexte
    model_class = TestAuthor
    introspector = ModelIntrospector()

    # Act - Exécution de l'action à tester
    analysis_result = introspector.analyze_model(model_class)

    # Assert - Vérification des résultats
    assert analysis_result is not None
    assert analysis_result.model_name == 'TestAuthor'
    assert 'first_name' in analysis_result.fields
    assert analysis_result.fields['first_name']['type'] == 'CharField'
```

### 3. Nommage Descriptif

```python
# ✅ Bon - Descriptif et spécifique
def test_type_generator_creates_graphql_type_for_django_model_with_foreign_keys():
    pass

def test_query_generator_handles_pagination_with_custom_page_size():
    pass

def test_mutation_generator_validates_required_fields_before_creation():
    pass

# ❌ Éviter - Trop générique
def test_generator():
    pass

def test_model():
    pass

def test_graphql():
    pass
```

## 🏗️ Structure des Tests

### Organisation des Fichiers

```python
# tests/test_core/test_model_introspector.py

"""
Tests pour le composant ModelIntrospector.

Ce module teste:
- Analyse des modèles Django
- Détection des champs et relations
- Gestion des méthodes métier
- Cas d'erreur et validation
"""

import pytest
from django.db import models
from rail_django_graphql.core.introspector import ModelIntrospector
from tests.fixtures.test_data_fixtures import TestAuthor, TestBook


class TestModelIntrospectorBasics:
    """Tests de base pour ModelIntrospector."""

    def test_analyze_simple_model(self):
        """Test d'analyse d'un modèle simple."""
        pass

    def test_analyze_model_with_relationships(self):
        """Test d'analyse d'un modèle avec relations."""
        pass


class TestModelIntrospectorFields:
    """Tests de détection des champs."""

    def test_detect_char_field(self):
        """Test de détection d'un CharField."""
        pass

    def test_detect_foreign_key_field(self):
        """Test de détection d'une ForeignKey."""
        pass


class TestModelIntrospectorBusinessMethods:
    """Tests de détection des méthodes métier."""

    def test_detect_custom_methods(self):
        """Test de détection des méthodes personnalisées."""
        pass

    def test_ignore_private_methods(self):
        """Test d'ignorance des méthodes privées."""
        pass


class TestModelIntrospectorErrorHandling:
    """Tests de gestion d'erreurs."""

    def test_handle_invalid_model(self):
        """Test de gestion d'un modèle invalide."""
        pass

    def test_handle_missing_model(self):
        """Test de gestion d'un modèle manquant."""
        pass
```

### Groupement par Fonctionnalité

```python
class TestTypeGeneratorCreation:
    """Tests de création de types GraphQL."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration commune pour tous les tests de cette classe."""
        self.generator = TypeGenerator()
        self.test_model = TestAuthor

    def test_create_basic_type(self):
        """Test de création d'un type de base."""
        graphql_type = self.generator.create_type(self.test_model)

        assert graphql_type is not None
        assert graphql_type._meta.name == 'TestAuthorType'

    def test_create_type_with_custom_fields(self):
        """Test de création avec champs personnalisés."""
        custom_fields = ['name', 'email']
        graphql_type = self.generator.create_type(
            self.test_model,
            include_fields=custom_fields
        )

        type_fields = graphql_type._meta.fields.keys()
        assert all(field in type_fields for field in custom_fields)
```

## 🔄 Patterns de Test

### 1. Pattern Factory

```python
# tests/fixtures/factories.py

import factory
from factory.django import DjangoModelFactory
from tests.fixtures.test_data_fixtures import TestAuthor, TestBook


class TestAuthorFactory(DjangoModelFactory):
    """Factory pour créer des auteurs de test."""

    class Meta:
        model = TestAuthor

    first_name = factory.Faker('first_name', locale='fr_FR')
    last_name = factory.Faker('last_name', locale='fr_FR')
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com"
    )
    bio = factory.Faker('text', max_nb_chars=200, locale='fr_FR')


class TestBookFactory(DjangoModelFactory):
    """Factory pour créer des livres de test."""

    class Meta:
        model = TestBook

    title = factory.Faker('sentence', nb_words=4, locale='fr_FR')
    author = factory.SubFactory(TestAuthorFactory)
    isbn = factory.Faker('isbn13')
    publication_date = factory.Faker('date_this_decade')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)


# Utilisation dans les tests
def test_book_creation_with_factory():
    """Test de création de livre avec factory."""
    book = TestBookFactory()

    assert book.title is not None
    assert book.author is not None
    assert book.isbn is not None
```

### 2. Pattern Builder

```python
class GraphQLQueryBuilder:
    """Builder pour construire des requêtes GraphQL de test."""

    def __init__(self):
        self.query_parts = []
        self.variables = {}

    def add_field(self, field_name, sub_fields=None):
        """Ajoute un champ à la requête."""
        if sub_fields:
            field_str = f"{field_name} {{ {' '.join(sub_fields)} }}"
        else:
            field_str = field_name

        self.query_parts.append(field_str)
        return self

    def add_variable(self, name, value, var_type):
        """Ajoute une variable à la requête."""
        self.variables[name] = value
        return self

    def build(self):
        """Construit la requête finale."""
        query_body = ' '.join(self.query_parts)
        return f"query {{ {query_body} }}", self.variables


# Utilisation
def test_complex_graphql_query():
    """Test d'une requête GraphQL complexe."""
    query, variables = (
        GraphQLQueryBuilder()
        .add_field('authors', ['id', 'name', 'email'])
        .add_field('books', ['title', 'isbn'])
        .build()
    )

    result = execute_graphql_query(query, variables)
    assert_graphql_success(result)
```

### 3. Pattern Parametrized Tests

```python
@pytest.mark.parametrize("field_type,expected_graphql_type", [
    (models.CharField, 'String'),
    (models.IntegerField, 'Int'),
    (models.BooleanField, 'Boolean'),
    (models.DateTimeField, 'DateTime'),
    (models.DecimalField, 'Decimal'),
])
def test_field_type_mapping(field_type, expected_graphql_type):
    """Test de mapping des types de champs Django vers GraphQL."""
    generator = TypeGenerator()

    # Créer un modèle de test dynamique
    test_field = field_type()
    graphql_type = generator.map_django_field_to_graphql(test_field)

    assert graphql_type == expected_graphql_type


@pytest.mark.parametrize("model_data,expected_validation", [
    ({'name': 'Valid Name', 'email': 'test@example.com'}, True),
    ({'name': '', 'email': 'test@example.com'}, False),
    ({'name': 'Valid Name', 'email': 'invalid-email'}, False),
    ({'name': None, 'email': 'test@example.com'}, False),
])
def test_model_validation(model_data, expected_validation):
    """Test de validation des données de modèle."""
    validator = ModelValidator()

    is_valid = validator.validate(TestAuthor, model_data)

    assert is_valid == expected_validation
```

## 🧩 Tests par Composant

### ModelIntrospector

```python
class TestModelIntrospector:
    """Tests complets pour ModelIntrospector."""

    @pytest.fixture
    def introspector(self):
        """Fixture pour ModelIntrospector."""
        return ModelIntrospector()

    def test_get_model_fields(self, introspector):
        """Test de récupération des champs d'un modèle."""
        fields = introspector.get_model_fields(TestAuthor)

        # Vérifier la présence des champs attendus
        expected_fields = ['id', 'first_name', 'last_name', 'email', 'bio']
        for field_name in expected_fields:
            assert field_name in fields

        # Vérifier les types de champs
        assert fields['first_name']['type'] == 'CharField'
        assert fields['email']['type'] == 'EmailField'

    def test_get_model_relationships(self, introspector):
        """Test de récupération des relations d'un modèle."""
        relationships = introspector.get_model_relationships(TestBook)

        assert 'author' in relationships
        assert relationships['author']['type'] == 'ForeignKey'
        assert relationships['author']['related_model'] == TestAuthor

    def test_get_business_methods(self, introspector):
        """Test de détection des méthodes métier."""
        methods = introspector.get_business_methods(TestAuthor)

        # Vérifier la présence des méthodes personnalisées
        assert 'get_full_name' in methods
        assert 'get_book_count' in methods

        # Vérifier l'absence des méthodes système
        assert 'save' not in methods
        assert '__str__' not in methods

    @pytest.mark.parametrize("invalid_input", [
        None,
        "not_a_model",
        123,
        [],
    ])
    def test_handle_invalid_model_input(self, introspector, invalid_input):
        """Test de gestion des entrées invalides."""
        with pytest.raises(ValueError, match="Invalid model"):
            introspector.analyze_model(invalid_input)
```

### TypeGenerator

```python
class TestTypeGenerator:
    """Tests pour TypeGenerator."""

    @pytest.fixture
    def generator(self):
        """Fixture pour TypeGenerator."""
        return TypeGenerator()

    def test_generate_basic_type(self, generator):
        """Test de génération d'un type de base."""
        graphql_type = generator.generate_type(TestAuthor)

        # Vérifier la structure du type
        assert graphql_type is not None
        assert hasattr(graphql_type, '_meta')
        assert graphql_type._meta.name == 'TestAuthorType'

        # Vérifier les champs
        fields = graphql_type._meta.fields
        assert 'first_name' in fields
        assert 'last_name' in fields
        assert 'email' in fields

    def test_generate_type_with_relationships(self, generator):
        """Test de génération avec relations."""
        graphql_type = generator.generate_type(TestBook)

        fields = graphql_type._meta.fields
        assert 'author' in fields

        # Vérifier que la relation est correctement typée
        author_field = fields['author']
        assert hasattr(author_field, 'type')

    def test_generate_type_with_custom_resolvers(self, generator):
        """Test de génération avec résolveurs personnalisés."""
        custom_resolvers = {
            'full_name': lambda obj, info: f"{obj.first_name} {obj.last_name}"
        }

        graphql_type = generator.generate_type(
            TestAuthor,
            custom_resolvers=custom_resolvers
        )

        assert 'full_name' in graphql_type._meta.fields

    def test_exclude_fields(self, generator):
        """Test d'exclusion de champs."""
        excluded_fields = ['bio', 'email']

        graphql_type = generator.generate_type(
            TestAuthor,
            exclude_fields=excluded_fields
        )

        fields = graphql_type._meta.fields
        for field in excluded_fields:
            assert field not in fields
```

### QueryGenerator

```python
class TestQueryGenerator:
    """Tests pour QueryGenerator."""

    @pytest.fixture
    def generator(self):
        """Fixture pour QueryGenerator."""
        return QueryGenerator()

    def test_generate_list_query(self, generator):
        """Test de génération de requête de liste."""
        query_field = generator.generate_list_query(TestAuthor)

        assert query_field is not None
        assert hasattr(query_field, 'type')

        # Tester l'exécution de la requête
        resolver = query_field.resolver
        assert callable(resolver)

    def test_generate_single_query(self, generator):
        """Test de génération de requête unitaire."""
        query_field = generator.generate_single_query(TestAuthor)

        assert query_field is not None

        # Vérifier les arguments (id requis)
        args = query_field.args
        assert 'id' in args

    def test_generate_filtered_query(self, generator):
        """Test de génération de requête avec filtres."""
        filters = ['name__icontains', 'email__exact']

        query_field = generator.generate_filtered_query(
            TestAuthor,
            filters=filters
        )

        # Vérifier la présence des arguments de filtre
        args = query_field.args
        for filter_name in filters:
            assert filter_name in args

    def test_generate_paginated_query(self, generator):
        """Test de génération de requête paginée."""
        query_field = generator.generate_paginated_query(TestAuthor)

        # Vérifier les arguments de pagination
        args = query_field.args
        assert 'first' in args  # Pagination Relay
        assert 'after' in args
```

## 📊 Gestion des Données

### Fixtures Réutilisables

```python
@pytest.fixture
def sample_authors():
    """Crée un échantillon d'auteurs pour les tests."""
    authors = []
    for i in range(5):
        author = TestAuthor.objects.create(
            first_name=f"Prénom{i}",
            last_name=f"Nom{i}",
            email=f"auteur{i}@example.com",
            bio=f"Biographie de l'auteur {i}"
        )
        authors.append(author)
    return authors


@pytest.fixture
def books_with_authors(sample_authors):
    """Crée des livres avec leurs auteurs."""
    books = []
    for i, author in enumerate(sample_authors):
        book = TestBook.objects.create(
            title=f"Livre {i}",
            author=author,
            isbn=f"978-2-1234-567{i}-0",
            publication_date=date(2020 + i, 1, 1),
            price=Decimal(f"{10 + i}.99")
        )
        books.append(book)
    return books


@pytest.fixture
def complex_dataset():
    """Crée un jeu de données complexe pour les tests d'intégration."""
    # Créer des catégories
    categories = [
        TestCategory.objects.create(name="Fiction", description="Livres de fiction"),
        TestCategory.objects.create(name="Science", description="Livres scientifiques"),
    ]

    # Créer des auteurs
    authors = TestAuthorFactory.create_batch(10)

    # Créer des livres avec relations
    books = []
    for i, author in enumerate(authors):
        book = TestBookFactory(
            author=author,
            category=categories[i % len(categories)]
        )
        books.append(book)

    # Créer des critiques
    reviews = []
    for book in books:
        for j in range(3):  # 3 critiques par livre
            review = TestReview.objects.create(
                book=book,
                rating=4 + (j % 2),  # Notes entre 4 et 5
                comment=f"Critique {j} pour {book.title}"
            )
            reviews.append(review)

    return {
        'categories': categories,
        'authors': authors,
        'books': books,
        'reviews': reviews,
    }
```

### Nettoyage des Données

```python
@pytest.fixture(autouse=True)
def clean_database():
    """Nettoie la base de données avant et après chaque test."""
    # Nettoyage avant le test
    TestReview.objects.all().delete()
    TestBook.objects.all().delete()
    TestAuthor.objects.all().delete()
    TestCategory.objects.all().delete()

    yield  # Exécution du test

    # Nettoyage après le test
    TestReview.objects.all().delete()
    TestBook.objects.all().delete()
    TestAuthor.objects.all().delete()
    TestCategory.objects.all().delete()


@pytest.fixture
def isolated_test():
    """Fixture pour tests nécessitant une isolation complète."""
    from django.db import transaction

    with transaction.atomic():
        # Créer un savepoint
        sid = transaction.savepoint()

        yield

        # Rollback au savepoint
        transaction.savepoint_rollback(sid)
```

## ✅ Assertions et Validations

### Assertions GraphQL Personnalisées

```python
def assert_graphql_success(result):
    """Vérifie qu'une requête GraphQL a réussi."""
    assert result is not None, "Le résultat ne doit pas être None"
    assert not result.errors, f"La requête ne doit pas avoir d'erreurs: {result.errors}"
    assert result.data is not None, "Les données ne doivent pas être None"


def assert_graphql_error(result, expected_error_message=None):
    """Vérifie qu'une requête GraphQL a échoué avec l'erreur attendue."""
    assert result is not None, "Le résultat ne doit pas être None"
    assert result.errors, "La requête doit avoir des erreurs"

    if expected_error_message:
        error_messages = [str(error) for error in result.errors]
        assert any(
            expected_error_message in msg for msg in error_messages
        ), f"Message d'erreur attendu '{expected_error_message}' non trouvé dans {error_messages}"


def assert_schema_has_type(schema, type_name):
    """Vérifie qu'un schéma contient un type spécifique."""
    type_map = schema.type_map
    assert type_name in type_map, f"Type '{type_name}' non trouvé dans le schéma"


def assert_type_has_field(graphql_type, field_name):
    """Vérifie qu'un type GraphQL contient un champ spécifique."""
    fields = graphql_type._meta.fields
    assert field_name in fields, f"Champ '{field_name}' non trouvé dans le type"


def assert_field_type(graphql_type, field_name, expected_type):
    """Vérifie le type d'un champ GraphQL."""
    fields = graphql_type._meta.fields
    assert field_name in fields, f"Champ '{field_name}' non trouvé"

    field = fields[field_name]
    actual_type = type(field.type).__name__
    assert actual_type == expected_type, f"Type attendu '{expected_type}', obtenu '{actual_type}'"
```

### Validations de Performance

```python
def assert_execution_time_under(max_seconds):
    """Décorateur pour vérifier le temps d'exécution."""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = test_func(*args, **kwargs)
            execution_time = time.time() - start_time

            assert execution_time < max_seconds, \
                f"Test trop lent: {execution_time:.2f}s > {max_seconds}s"

            return result
        return wrapper
    return decorator


def assert_memory_usage_under(max_mb):
    """Décorateur pour vérifier l'utilisation mémoire."""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            result = test_func(*args, **kwargs)

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before

            assert memory_used < max_mb, \
                f"Utilisation mémoire excessive: {memory_used:.2f}MB > {max_mb}MB"

            return result
        return wrapper
    return decorator


# Utilisation
@assert_execution_time_under(2.0)  # Max 2 secondes
@assert_memory_usage_under(50)     # Max 50MB
def test_large_schema_generation():
    """Test de génération d'un grand schéma."""
    generator = AutoSchemaGenerator()
    schema = generator.generate_schema(large_model_list)
    assert schema is not None
```

## ⚡ Performance et Optimisation

### Tests de Performance

```python
class TestPerformance:
    """Tests de performance pour les composants critiques."""

    @pytest.mark.performance
    def test_schema_generation_performance(self):
        """Test de performance de génération de schéma."""
        models = [TestAuthor, TestBook, TestCategory, TestReview]

        with PerformanceProfiler() as profiler:
            generator = AutoSchemaGenerator()
            schema = generator.generate_schema(models)

        # Assertions de performance
        assert profiler.execution_time < 5.0, "Génération trop lente"
        assert profiler.memory_usage < 100 * 1024 * 1024, "Utilisation mémoire excessive"
        assert schema is not None

    @pytest.mark.performance
    def test_query_execution_performance(self):
        """Test de performance d'exécution de requêtes."""
        # Créer un jeu de données conséquent
        TestAuthorFactory.create_batch(1000)

        query = """
        query {
            authors {
                id
                firstName
                lastName
                books {
                    title
                    isbn
                }
            }
        }
        """

        with DatabaseQueryCounter() as counter:
            with PerformanceProfiler() as profiler:
                result = execute_graphql_query(query)

        # Vérifications de performance
        assert_graphql_success(result)
        assert profiler.execution_time < 2.0, "Requête trop lente"
        assert counter.query_count < 10, "Trop de requêtes DB (N+1 problem?)"
```

### Optimisation des Tests

```python
# Utilisation de mocks pour les tests unitaires
@pytest.fixture
def mock_database():
    """Mock de la base de données pour les tests unitaires."""
    with patch('django.db.models.QuerySet') as mock_qs:
        mock_qs.all.return_value = []
        mock_qs.filter.return_value = mock_qs
        mock_qs.get.return_value = TestAuthor(id=1, first_name="Test")
        yield mock_qs


def test_introspector_with_mock_db(mock_database):
    """Test unitaire avec base de données mockée."""
    introspector = ModelIntrospector()

    # Le test s'exécute sans accès réel à la DB
    result = introspector.get_model_instances(TestAuthor)

    assert result is not None
    mock_database.all.assert_called_once()


# Cache des fixtures coûteuses
@pytest.fixture(scope="session")
def expensive_dataset():
    """Dataset coûteux partagé entre tous les tests de la session."""
    # Cette fixture n'est créée qu'une fois par session de test
    return create_large_test_dataset()


# Tests en parallèle avec isolation
@pytest.mark.django_db(transaction=True)
def test_concurrent_schema_generation():
    """Test de génération de schéma en parallèle."""
    import threading

    results = []
    errors = []

    def generate_schema():
        try:
            generator = AutoSchemaGenerator()
            schema = generator.generate_schema([TestAuthor])
            results.append(schema)
        except Exception as e:
            errors.append(e)

    # Lancer plusieurs threads
    threads = [threading.Thread(target=generate_schema) for _ in range(5)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Vérifications
    assert len(errors) == 0, f"Erreurs en parallèle: {errors}"
    assert len(results) == 5, "Tous les schémas doivent être générés"
    assert all(schema is not None for schema in results)
```

## 📝 Exemples Pratiques

### Test d'Intégration Complet

```python
@pytest.mark.integration
def test_complete_graphql_workflow(complex_dataset):
    """Test du workflow complet de génération et exécution GraphQL."""

    # 1. Génération du schéma
    models = [TestAuthor, TestBook, TestCategory, TestReview]
    generator = AutoSchemaGenerator()
    schema = generator.generate_schema(models)

    assert_schema_has_type(schema, 'TestAuthorType')
    assert_schema_has_type(schema, 'TestBookType')

    # 2. Exécution d'une requête complexe
    query = """
    query {
        authors {
            id
            firstName
            lastName
            books {
                title
                category {
                    name
                }
                reviews {
                    rating
                    comment
                }
            }
        }
    }
    """

    client = GraphQLTestClient(schema)
    result = client.execute(query)

    assert_graphql_success(result)

    # 3. Validation des données
    authors_data = result.data['authors']
    assert len(authors_data) > 0

    for author_data in authors_data:
        assert 'id' in author_data
        assert 'firstName' in author_data
        assert 'books' in author_data

        for book_data in author_data['books']:
            assert 'title' in book_data
            assert 'category' in book_data
            assert 'reviews' in book_data

    # 4. Test d'une mutation
    mutation = """
    mutation CreateAuthor($firstName: String!, $lastName: String!, $email: String!) {
        createAuthor(firstName: $firstName, lastName: $lastName, email: $email) {
            author {
                id
                firstName
                lastName
                email
            }
            success
            errors
        }
    }
    """

    variables = {
        'firstName': 'Nouvel',
        'lastName': 'Auteur',
        'email': 'nouvel.auteur@example.com'
    }

    mutation_result = client.execute(mutation, variables)
    assert_graphql_success(mutation_result)

    create_data = mutation_result.data['createAuthor']
    assert create_data['success'] is True
    assert len(create_data['errors']) == 0
    assert create_data['author']['firstName'] == 'Nouvel'
```

### Test de Cas Limite

```python
@pytest.mark.edge_cases
class TestEdgeCases:
    """Tests des cas limites et situations exceptionnelles."""

    def test_empty_model_list(self):
        """Test avec une liste de modèles vide."""
        generator = AutoSchemaGenerator()

        with pytest.raises(ValueError, match="Au moins un modèle requis"):
            generator.generate_schema([])

    def test_model_with_circular_relationships(self):
        """Test avec des relations circulaires."""
        # Créer des modèles avec relations circulaires
        class ModelA(models.Model):
            name = models.CharField(max_length=100)
            b_ref = models.ForeignKey('ModelB', on_delete=models.CASCADE, null=True)

            class Meta:
                app_label = 'tests'

        class ModelB(models.Model):
            name = models.CharField(max_length=100)
            a_ref = models.ForeignKey(ModelA, on_delete=models.CASCADE, null=True)

            class Meta:
                app_label = 'tests'

        generator = AutoSchemaGenerator()

        # Ne doit pas lever d'exception (récursion infinie)
        schema = generator.generate_schema([ModelA, ModelB])
        assert schema is not None

    def test_model_with_very_long_field_names(self):
        """Test avec des noms de champs très longs."""
        long_field_name = 'a' * 200  # 200 caractères

        # Créer dynamiquement un modèle avec un champ au nom très long
        attrs = {
            long_field_name: models.CharField(max_length=100),
            '__module__': 'tests.models',
            'Meta': type('Meta', (), {'app_label': 'tests'})
        }

        LongFieldModel = type('LongFieldModel', (models.Model,), attrs)

        generator = TypeGenerator()
        graphql_type = generator.generate_type(LongFieldModel)

        # Vérifier que le champ est présent (possiblement tronqué)
        fields = graphql_type._meta.fields
        assert len(fields) > 0

    def test_model_with_special_characters_in_names(self):
        """Test avec des caractères spéciaux dans les noms."""
        # Modèle avec des caractères spéciaux (accents, etc.)
        class ModèleAvecAccents(models.Model):
            nom_avec_accents = models.CharField(max_length=100, verbose_name="Nom avec accents")

            class Meta:
                app_label = 'tests'
                verbose_name = "Modèle avec accents"

        generator = TypeGenerator()
        graphql_type = generator.generate_type(ModèleAvecAccents)

        # Vérifier que les noms sont correctement normalisés
        assert graphql_type._meta.name is not None
        assert 'nom_avec_accents' in graphql_type._meta.fields

    @pytest.mark.parametrize("invalid_query", [
        "{ invalid_field }",
        "{ authors { non_existent_field } }",
        "mutation { invalidMutation }",
        "{ authors( invalidArg: true ) { id } }",
    ])
    def test_invalid_graphql_queries(self, invalid_query):
        """Test de requêtes GraphQL invalides."""
        from tests.schema import schema

        client = GraphQLTestClient(schema)
        result = client.execute(invalid_query)

        # Doit avoir des erreurs
        assert_graphql_error(result)
```

Ce guide fournit une base solide pour écrire des tests efficaces et maintenables. Adaptez ces patterns et exemples selon les besoins spécifiques de votre projet.
