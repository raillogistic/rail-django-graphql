# Guide de Tests - Django GraphQL Auto

Ce guide fournit une documentation complète pour l'exécution et la maintenance des tests du projet Django GraphQL Auto.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Configuration](#configuration)
- [Structure des Tests](#structure-des-tests)
- [Exécution des Tests](#exécution-des-tests)
- [Types de Tests](#types-de-tests)
- [Fixtures et Utilitaires](#fixtures-et-utilitaires)
- [Rapports et Métriques](#rapports-et-métriques)
- [Bonnes Pratiques](#bonnes-pratiques)
- [Dépannage](#dépannage)

## 🎯 Vue d'ensemble

La suite de tests de Django GraphQL Auto est conçue pour garantir la qualité, la performance et la fiabilité du système de génération automatique de schémas GraphQL.

### Objectifs des Tests

- **Qualité du Code** : Validation de la logique métier et des fonctionnalités
- **Performance** : Mesure des temps d'exécution et de l'utilisation mémoire
- **Fiabilité** : Tests de concurrence et de gestion d'erreurs
- **Sécurité** : Validation des mécanismes de protection
- **Régression** : Prévention des régressions lors des modifications

### Couverture de Tests

- ✅ **Tests Unitaires** : Composants individuels
- ✅ **Tests d'Intégration** : Workflow complet
- ✅ **Tests de Performance** : Optimisation et scalabilité
- ✅ **Tests de Sécurité** : Vulnérabilités et protections
- ✅ **Tests de Régression** : Stabilité des fonctionnalités

## ⚙️ Configuration

### Prérequis

```bash
# Installation des dépendances de test
pip install pytest pytest-django pytest-cov pytest-xdist
pip install factory-boy faker
pip install coverage[toml]
```

### Variables d'Environnement

```bash
# Configuration de base
export DJANGO_SETTINGS_MODULE=tests.settings
export TESTING=True

# Configuration optionnelle
export DEBUG=False
export DATABASE_URL=sqlite:///test.db
```

### Configuration Django

Le fichier `tests/settings.py` contient la configuration spécifique aux tests :

```python
# Base de données en mémoire pour les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Cache local pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## 🏗️ Structure des Tests

```
tests/
├── __init__.py                 # Configuration du package de tests
├── settings.py                 # Configuration Django pour les tests
├── conftest.py                 # Configuration pytest globale
├── urls.py                     # URLs de test
├── schema.py                   # Schéma GraphQL de test
├── models.py                   # Modèles de test
├── apps.py                     # Configuration de l'app de test
├── admin.py                    # Interface admin pour les tests
├── views.py                    # Vues de test et utilitaires
│
├── fixtures/                   # Fixtures et utilitaires
│   ├── __init__.py
│   ├── test_data_fixtures.py   # Données de test
│   ├── test_utilities.py       # Utilitaires de test
│   ├── mocks_and_stubs.py      # Mocks et stubs
│   └── assertion_helpers.py    # Helpers d'assertion
│
├── test_core/                  # Tests des composants principaux
│   ├── __init__.py
│   ├── test_model_introspector.py
│   ├── test_type_generator.py
│   ├── test_query_generator.py
│   └── test_mutation_generator.py
│
├── test_generators/            # Tests des générateurs
│   ├── __init__.py
│   ├── test_schema_generator.py
│   ├── test_field_resolver.py
│   └── test_relationship_handler.py
│
├── test_integration/           # Tests d'intégration
│   ├── __init__.py
│   ├── test_complete_workflow.py
│   ├── test_django_integration.py
│   └── test_graphql_execution.py
│
├── test_business_methods/      # Tests des méthodes métier
│   ├── __init__.py
│   ├── test_method_detection.py
│   ├── test_method_integration.py
│   └── test_custom_resolvers.py
│
├── test_edge_cases/            # Tests des cas limites
│   ├── __init__.py
│   ├── test_error_handling.py
│   ├── test_invalid_models.py
│   └── test_complex_relationships.py
│
├── test_performance/           # Tests de performance
│   ├── __init__.py
│   ├── test_memory_usage.py
│   ├── test_query_optimization.py
│   └── test_concurrent_requests.py
│
└── management/                 # Commandes de gestion
    └── commands/
        └── run_test_suite.py   # Commande d'exécution complète
```

## 🚀 Exécution des Tests

### Commandes de Base

```bash
# Exécution de tous les tests
pytest

# Tests avec couverture
pytest --cov=django_graphql_auto --cov-report=html

# Tests en parallèle
pytest -n auto

# Tests avec rapport détaillé
pytest -v --tb=short

# Tests d'un module spécifique
pytest tests/test_core/

# Tests avec tags
pytest -m "unit"
pytest -m "not slow"
```

### Commande de Gestion Django

```bash
# Exécution complète avec rapports
python manage.py run_test_suite --coverage --performance

# Tests avec configuration personnalisée
python manage.py run_test_suite \
    --parallel 4 \
    --output-dir reports \
    --exclude-tags slow
```

### Configuration pytest.ini

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = tests.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = 
    --reuse-db
    --nomigrations
    --cov=django_graphql_auto
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --maxfail=5
    --tb=short
markers =
    unit: Tests unitaires
    integration: Tests d'intégration
    performance: Tests de performance
    slow: Tests lents
    database: Tests nécessitant la base de données
```

## 🧪 Types de Tests

### Tests Unitaires

Tests des composants individuels en isolation.

```python
@pytest.mark.unit
def test_model_introspector_get_fields():
    """Test de récupération des champs d'un modèle."""
    introspector = ModelIntrospector()
    fields = introspector.get_fields(TestModel)
    
    assert 'name' in fields
    assert fields['name']['type'] == 'CharField'
```

### Tests d'Intégration

Tests du workflow complet de génération de schéma.

```python
@pytest.mark.integration
def test_complete_schema_generation():
    """Test de génération complète d'un schéma."""
    generator = AutoSchemaGenerator()
    schema = generator.generate_schema([TestModel])
    
    assert schema is not None
    assert_schema_has_type(schema, 'TestModelType')
```

### Tests de Performance

Mesure des performances et de l'utilisation des ressources.

```python
@pytest.mark.performance
def test_schema_generation_performance():
    """Test de performance de génération de schéma."""
    with PerformanceProfiler() as profiler:
        generator = AutoSchemaGenerator()
        schema = generator.generate_schema(large_model_list)
    
    assert profiler.execution_time < 5.0  # 5 secondes max
    assert profiler.memory_usage < 100 * 1024 * 1024  # 100MB max
```

### Tests de Sécurité

Validation des mécanismes de sécurité.

```python
@pytest.mark.security
def test_sql_injection_protection():
    """Test de protection contre l'injection SQL."""
    malicious_query = "'; DROP TABLE users; --"
    
    with pytest.raises(ValidationError):
        execute_graphql_query(malicious_query)
```

## 🔧 Fixtures et Utilitaires

### Fixtures de Données

```python
@pytest.fixture
def sample_authors():
    """Crée des auteurs de test."""
    return AuthorFactory.create_batch(5)

@pytest.fixture
def complete_dataset():
    """Crée un jeu de données complet."""
    return create_complete_test_dataset()
```

### Utilitaires de Test

```python
# Client GraphQL de test
client = GraphQLTestClient(schema)
result = client.execute(query, variables)

# Assertions GraphQL
assert_graphql_success(result)
assert_graphql_error(result, "Field not found")

# Profiling de performance
with PerformanceProfiler() as profiler:
    # Code à profiler
    pass
```

### Mocks et Stubs

```python
@pytest.fixture
def mock_model_introspector():
    """Mock du ModelIntrospector."""
    with patch('django_graphql_auto.core.ModelIntrospector') as mock:
        mock.return_value.get_fields.return_value = {}
        yield mock
```

## 📊 Rapports et Métriques

### Rapport de Couverture

```bash
# Génération du rapport HTML
pytest --cov=django_graphql_auto --cov-report=html

# Rapport dans le terminal
pytest --cov=django_graphql_auto --cov-report=term-missing

# Rapport XML (pour CI/CD)
pytest --cov=django_graphql_auto --cov-report=xml
```

### Métriques de Performance

Les tests de performance génèrent des métriques détaillées :

- **Temps d'exécution** : Durée des opérations
- **Utilisation mémoire** : Consommation RAM
- **Requêtes DB** : Nombre et optimisation
- **Concurrence** : Performance sous charge

### Rapports Personnalisés

```bash
# Génération de rapports complets
python manage.py run_test_suite \
    --coverage \
    --performance \
    --output-dir reports/$(date +%Y%m%d_%H%M%S)
```

## ✅ Bonnes Pratiques

### Écriture de Tests

1. **Nommage Descriptif**
   ```python
   def test_model_introspector_handles_foreign_key_relationships():
       """Test spécifique et descriptif."""
   ```

2. **Structure AAA (Arrange, Act, Assert)**
   ```python
   def test_example():
       # Arrange
       model = TestModel.objects.create(name="test")
       
       # Act
       result = introspector.analyze(model)
       
       # Assert
       assert result.is_valid
   ```

3. **Tests Indépendants**
   - Chaque test doit être indépendant
   - Utiliser des fixtures pour l'isolation
   - Nettoyer après chaque test

4. **Assertions Claires**
   ```python
   # Bon
   assert user.is_active is True
   assert len(results) == 3
   
   # Éviter
   assert user
   assert results
   ```

### Performance des Tests

1. **Tests Rapides**
   - Utiliser des mocks pour les dépendances externes
   - Base de données en mémoire
   - Éviter les sleep() inutiles

2. **Parallélisation**
   ```bash
   pytest -n auto  # Utilise tous les CPU disponibles
   ```

3. **Réutilisation de DB**
   ```bash
   pytest --reuse-db  # Réutilise la DB entre les exécutions
   ```

### Organisation

1. **Groupement Logique**
   - Tests par composant
   - Tests par fonctionnalité
   - Tests par niveau (unit/integration)

2. **Tags et Marqueurs**
   ```python
   @pytest.mark.slow
   @pytest.mark.database
   def test_complex_operation():
       pass
   ```

3. **Documentation**
   - Docstrings explicatives
   - Commentaires pour la logique complexe
   - README pour chaque module de test

## 🔍 Dépannage

### Problèmes Courants

#### Tests Lents

```bash
# Identifier les tests lents
pytest --durations=10

# Exclure les tests lents
pytest -m "not slow"
```

#### Erreurs de Base de Données

```python
# Forcer la création d'une nouvelle DB
pytest --create-db

# Réinitialiser les migrations
pytest --nomigrations
```

#### Problèmes de Mémoire

```python
# Profiler l'utilisation mémoire
pytest --memprof

# Limiter les tests en parallèle
pytest -n 2  # Au lieu de -n auto
```

#### Erreurs de Concurrence

```python
# Tests séquentiels pour le débogage
pytest --forked

# Isolation des tests
pytest --lf  # Derniers échecs seulement
```

### Débogage

```python
# Mode debug
pytest -s --pdb

# Logs détaillés
pytest --log-cli-level=DEBUG

# Arrêt au premier échec
pytest -x
```

### Outils de Diagnostic

```bash
# Informations système
python manage.py run_test_suite --debug-mode

# Vérification de santé
curl http://localhost:8000/test/health/

# Métriques en temps réel
curl http://localhost:8000/test/status/
```

## 📚 Ressources Supplémentaires

- [Documentation pytest](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [GraphQL Testing Best Practices](https://graphql.org/learn/testing/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

## 🤝 Contribution

Pour contribuer aux tests :

1. Suivre les conventions de nommage
2. Ajouter des tests pour les nouvelles fonctionnalités
3. Maintenir la couverture > 80%
4. Documenter les tests complexes
5. Exécuter la suite complète avant commit

```bash
# Vérification avant commit
python manage.py run_test_suite --coverage --performance
```