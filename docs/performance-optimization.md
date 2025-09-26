# Guide d'Optimisation des Performances

Ce guide détaille le système complet d'optimisation des performances de Django GraphQL Auto, incluant la prévention des requêtes N+1, le cache multi-niveaux, et le monitoring des performances.

## Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Prévention des Requêtes N+1](#prévention-des-requêtes-n1)
3. [Système de Cache](#système-de-cache)
4. [Monitoring des Performances](#monitoring-des-performances)
5. [Configuration](#configuration)
6. [Benchmarks et Tests](#benchmarks-et-tests)
7. [Dépannage](#dépannage)

## Vue d'ensemble

Le système d'optimisation des performances de Django GraphQL Auto fournit:

- **Prévention automatique des requêtes N+1** avec `select_related` et `prefetch_related`
- **Cache multi-niveaux** (schéma, requête, champ)
- **Monitoring en temps réel** des performances
- **Analyse de complexité** des requêtes
- **Alertes automatiques** pour les problèmes de performance

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GraphQL Request                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Performance Middleware                         │
│  • Request tracking                                         │
│  • Metrics collection                                       │
│  • Alert generation                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Query Optimizer                              │
│  • N+1 prevention                                          │
│  • Complexity analysis                                     │
│  • Queryset optimization                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Cache Manager                                │
│  • Query result caching                                    │
│  • Field-level caching                                     │
│  • Intelligent invalidation                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Database Query                               │
└─────────────────────────────────────────────────────────────┘
```

## Prévention des Requêtes N+1

### Fonctionnement Automatique

Le système analyse automatiquement les requêtes GraphQL et applique les optimisations appropriées:

```python
from django_graphql_auto.extensions.optimization import optimize_query

class Query(ObjectType):
    books = List(BookType)
    
    @optimize_query()  # Optimisation automatique
    def resolve_books(self, info):
        return Book.objects.all()  # Sera automatiquement optimisé
```

### Configuration Manuelle

Pour un contrôle plus fin:

```python
from django_graphql_auto.extensions.optimization import QueryOptimizationConfig

config = QueryOptimizationConfig(
    enable_select_related=True,
    enable_prefetch_related=True,
    max_select_related_depth=3,
    max_prefetch_related_depth=2
)

@optimize_query(config=config)
def resolve_books(self, info):
    return Book.objects.all()
```

### Exemple d'Optimisation

**Avant optimisation** (requêtes N+1):
```python
# Cette requête génère N+1 requêtes
def resolve_books(self, info):
    books = Book.objects.all()  # 1 requête
    for book in books:
        print(book.author.name)  # N requêtes supplémentaires
```

**Après optimisation**:
```python
@optimize_query()
def resolve_books(self, info):
    # Le système applique automatiquement select_related('author')
    books = Book.objects.all()  # 1 seule requête avec JOIN
    for book in books:
        print(book.author.name)  # Pas de requête supplémentaire
```

## Système de Cache

### Configuration du Cache

```python
from django_graphql_auto.extensions.caching import CacheConfig

cache_config = CacheConfig(
    enabled=True,
    query_cache_enabled=True,
    field_cache_enabled=True,
    default_timeout=300,  # 5 minutes
    max_cache_size=1000,
    backend='redis'  # ou 'memcached', 'locmem'
)
```

### Cache de Requêtes

Cache les résultats complets des requêtes GraphQL:

```python
from django_graphql_auto.extensions.caching import cache_query

@cache_query(timeout=600, user_specific=True)
def resolve_books(self, info):
    return Book.objects.select_related('author').all()
```

### Cache de Champs

Cache les valeurs individuelles des champs:

```python
from django_graphql_auto.extensions.caching import cache_field

class BookType(ObjectType):
    expensive_calculation = String()
    
    @cache_field(timeout=3600)
    def resolve_expensive_calculation(self, info):
        # Calcul coûteux mis en cache
        return perform_expensive_calculation(self.id)
```

### Invalidation Intelligente

Le cache est automatiquement invalidé lors des modifications:

```python
# Lors de la sauvegarde d'un modèle
book = Book.objects.get(id=1)
book.title = "Nouveau titre"
book.save()  # Cache automatiquement invalidé
```

### Stratégies de Cache

#### 1. Cache par Utilisateur
```python
@cache_query(user_specific=True)
def resolve_user_books(self, info):
    user = info.context.user
    return Book.objects.filter(owner=user)
```

#### 2. Cache Global
```python
@cache_query(user_specific=False)
def resolve_public_books(self, info):
    return Book.objects.filter(is_public=True)
```

#### 3. Cache Conditionnel
```python
@cache_query(
    condition=lambda info: not info.context.user.is_staff,
    timeout=300
)
def resolve_books(self, info):
    return Book.objects.all()
```

## Monitoring des Performances

### Middleware de Performance

Ajoutez le middleware dans `settings.py`:

```python
MIDDLEWARE = [
    # ... autres middlewares
    'django_graphql_auto.middleware.performance.GraphQLPerformanceMiddleware',
]
```

### Métriques Collectées

Le système collecte automatiquement:

- **Temps d'exécution** des requêtes
- **Nombre de requêtes** de base de données
- **Utilisation mémoire**
- **Taux de cache hit/miss**
- **Complexité des requêtes**

### Alertes Automatiques

Configuration des alertes:

```python
from django_graphql_auto.middleware.performance import setup_performance_monitoring

setup_performance_monitoring(
    slow_query_threshold=2.0,  # 2 secondes
    high_memory_threshold=100.0,  # 100 MB
    max_db_queries=50,
    alert_handlers=['email', 'slack', 'webhook']
)
```

### API de Monitoring

Accédez aux métriques via l'API:

```python
# Dans urls.py
from django_graphql_auto.middleware.performance import GraphQLPerformanceView

urlpatterns = [
    path('graphql/performance/', GraphQLPerformanceView.as_view()),
]
```

Exemple de réponse:
```json
{
    "current_stats": {
        "total_requests": 1250,
        "avg_execution_time": 0.45,
        "cache_hit_ratio": 0.78,
        "slow_queries": 12
    },
    "recent_alerts": [
        {
            "type": "slow_query",
            "query": "books { author { reviews } }",
            "execution_time": 3.2,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    ]
}
```

## Configuration

### Configuration Complète

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'OPTIMIZATION': {
        'ENABLED': True,
        'N_PLUS_ONE_PREVENTION': {
            'ENABLED': True,
            'MAX_SELECT_RELATED_DEPTH': 3,
            'MAX_PREFETCH_RELATED_DEPTH': 2,
            'AUTO_OPTIMIZE_QUERYSETS': True
        },
        'QUERY_COMPLEXITY': {
            'ENABLED': True,
            'MAX_COMPLEXITY': 100,
            'MAX_DEPTH': 10,
            'TIMEOUT': 30  # secondes
        }
    },
    'CACHING': {
        'ENABLED': True,
        'BACKEND': 'redis',
        'QUERY_CACHE': {
            'ENABLED': True,
            'DEFAULT_TIMEOUT': 300,
            'MAX_SIZE': 1000
        },
        'FIELD_CACHE': {
            'ENABLED': True,
            'DEFAULT_TIMEOUT': 600,
            'MAX_SIZE': 5000
        },
        'INVALIDATION': {
            'AUTO_INVALIDATE_ON_SAVE': True,
            'AUTO_INVALIDATE_ON_DELETE': True
        }
    },
    'MONITORING': {
        'ENABLED': True,
        'COLLECT_METRICS': True,
        'SLOW_QUERY_THRESHOLD': 2.0,
        'HIGH_MEMORY_THRESHOLD': 100.0,
        'MAX_DB_QUERIES': 50,
        'ALERT_HANDLERS': ['email', 'webhook']
    }
}
```

### Configuration par Environnement

```python
# settings/production.py
DJANGO_GRAPHQL_AUTO['CACHING']['BACKEND'] = 'redis'
DJANGO_GRAPHQL_AUTO['MONITORING']['ENABLED'] = True

# settings/development.py
DJANGO_GRAPHQL_AUTO['CACHING']['BACKEND'] = 'locmem'
DJANGO_GRAPHQL_AUTO['MONITORING']['ENABLED'] = False
```

## Benchmarks et Tests

### Exécution des Benchmarks

```bash
# Tous les benchmarks
python manage.py run_performance_benchmarks

# Benchmark spécifique
python manage.py run_performance_benchmarks --test n_plus_one

# Avec options personnalisées
python manage.py run_performance_benchmarks \
    --data-sizes 10,50,100,500 \
    --output-dir ./results \
    --verbose
```

### Tests de Performance

```python
# tests/test_performance.py
from django.test import TestCase
from django_graphql_auto.extensions.optimization import optimize_query

class PerformanceTestCase(TestCase):
    def test_n_plus_one_prevention(self):
        @optimize_query()
        def optimized_resolver(root, info):
            return Book.objects.all()
        
        # Test que l'optimisation réduit le nombre de requêtes
        with self.assertNumQueries(1):  # Au lieu de N+1
            list(optimized_resolver(None, mock_info))
```

### Métriques de Benchmark

Les benchmarks génèrent des rapports détaillés:

- **Temps d'exécution** avant/après optimisation
- **Nombre de requêtes** de base de données
- **Utilisation mémoire**
- **Taux de cache hit**
- **Amélioration des performances** en pourcentage

## Dépannage

### Problèmes Courants

#### 1. Requêtes Toujours Lentes

**Symptôme**: Les requêtes restent lentes malgré l'optimisation.

**Solutions**:
```python
# Vérifier la configuration
from django_graphql_auto.extensions.optimization import get_optimizer
optimizer = get_optimizer()
print(optimizer.config.enable_select_related)  # Doit être True

# Forcer l'optimisation
@optimize_query(force_optimization=True)
def resolve_books(self, info):
    return Book.objects.all()
```

#### 2. Cache Non Fonctionnel

**Symptôme**: Le cache ne semble pas fonctionner.

**Solutions**:
```python
# Vérifier la configuration du cache Django
from django.core.cache import cache
cache.set('test', 'value', 60)
print(cache.get('test'))  # Doit retourner 'value'

# Vérifier les statistiques de cache
from django_graphql_auto.extensions.caching import get_cache_manager
stats = get_cache_manager().get_stats()
print(f"Hits: {stats.hits}, Misses: {stats.misses}")
```

#### 3. Alertes de Performance

**Symptôme**: Trop d'alertes de performance.

**Solutions**:
```python
# Ajuster les seuils
setup_performance_monitoring(
    slow_query_threshold=5.0,  # Plus tolérant
    high_memory_threshold=200.0,
    max_db_queries=100
)
```

### Debugging

#### Activer les Logs de Debug

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django_graphql_auto.optimization': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django_graphql_auto.caching': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

#### Analyser les Requêtes

```python
from django.db import connection
from django_graphql_auto.extensions.optimization import optimize_query

@optimize_query()
def resolve_books(self, info):
    queryset = Book.objects.all()
    print(f"SQL: {queryset.query}")  # Voir la requête SQL générée
    return queryset

# Après exécution
print(f"Nombre de requêtes: {len(connection.queries)}")
for query in connection.queries:
    print(f"SQL: {query['sql']}")
    print(f"Temps: {query['time']}")
```

### Optimisations Avancées

#### 1. Cache Personnalisé

```python
from django_graphql_auto.extensions.caching import GraphQLCacheManager

class CustomCacheManager(GraphQLCacheManager):
    def get_cache_key(self, query_string, variables, user_id):
        # Logique personnalisée pour les clés de cache
        return f"custom:{hash(query_string)}:{user_id}"
    
    def should_cache_query(self, query_string, variables, user_id):
        # Logique personnalisée pour décider du cache
        return 'expensive_field' in query_string
```

#### 2. Optimisation Conditionnelle

```python
@optimize_query(
    condition=lambda info: info.context.user.is_authenticated,
    enable_caching=lambda info: not info.context.user.is_staff
)
def resolve_books(self, info):
    return Book.objects.all()
```

#### 3. Monitoring Personnalisé

```python
from django_graphql_auto.middleware.performance import monitor_performance

@monitor_performance(
    track_memory=True,
    track_cache=True,
    custom_metrics=['custom_metric']
)
def expensive_operation():
    # Opération coûteuse
    pass
```

## Bonnes Pratiques

### 1. Configuration Progressive

Commencez avec une configuration de base et ajustez progressivement:

```python
# Phase 1: Optimisation de base
DJANGO_GRAPHQL_AUTO = {
    'OPTIMIZATION': {'ENABLED': True},
    'CACHING': {'ENABLED': False},  # Désactivé initialement
    'MONITORING': {'ENABLED': True}
}

# Phase 2: Ajout du cache
DJANGO_GRAPHQL_AUTO['CACHING']['ENABLED'] = True

# Phase 3: Optimisation fine
DJANGO_GRAPHQL_AUTO['CACHING']['FIELD_CACHE']['ENABLED'] = True
```

### 2. Tests de Performance Réguliers

```bash
# Exécuter les benchmarks régulièrement
python manage.py run_performance_benchmarks --test all
```

### 3. Monitoring en Production

```python
# Alertes pour la production
setup_performance_monitoring(
    slow_query_threshold=1.0,
    alert_handlers=['email', 'slack'],
    email_recipients=['admin@example.com'],
    slack_webhook='https://hooks.slack.com/...'
)
```

### 4. Documentation des Optimisations

Documentez vos optimisations personnalisées:

```python
@optimize_query(
    enable_caching=True,
    cache_timeout=3600,
    complexity_limit=50
)
def resolve_complex_books(self, info):
    """
    Résolveur optimisé pour les livres complexes.
    
    Optimisations appliquées:
    - Cache de 1 heure
    - Limite de complexité à 50
    - Prévention N+1 automatique
    """
    return Book.objects.select_related('author', 'publisher')
```

## Conclusion

Le système d'optimisation des performances de Django GraphQL Auto fournit une solution complète pour:

- **Améliorer automatiquement** les performances des requêtes GraphQL
- **Réduire la charge** sur la base de données
- **Monitorer en temps réel** les performances
- **Alerter** sur les problèmes potentiels

Avec une configuration appropriée et un monitoring régulier, vous pouvez obtenir des améliorations significatives des performances de votre API GraphQL.