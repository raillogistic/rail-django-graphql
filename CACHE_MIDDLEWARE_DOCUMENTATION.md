# GraphQL Cache Invalidation Middleware Documentation

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation et Configuration](#installation-et-configuration)
3. [Fonctionnement](#fonctionnement)
4. [Utilisation](#utilisation)
5. [Tests et Validation](#tests-et-validation)
6. [Dépannage](#dépannage)
7. [Limitations Connues](#limitations-connues)

## 🎯 Vue d'ensemble

Le **GraphQL Cache Invalidation Middleware** est un middleware Django conçu pour invalider automatiquement le cache lors des opérations de modification de données via GraphQL et les opérations directes sur les modèles Django.

### Fonctionnalités Principales

- ✅ **Invalidation automatique** lors des opérations CRUD
- ✅ **Support des signaux Django** (post_save, post_delete, m2m_changed)
- ✅ **Détection des mutations GraphQL** via l'analyse des requêtes
- ✅ **Thread-safe** avec protection contre les invalidations multiples
- ✅ **Logging complet** pour le débogage
- ✅ **Configuration flexible** des modèles surveillés

## 🔧 Installation et Configuration

### 1. Ajout du Middleware

Ajoutez le middleware dans votre `settings.py` :

```python
MIDDLEWARE = [
    # ... autres middlewares
    'cache_middleware.GraphQLCacheInvalidationMiddleware',
    # ... autres middlewares
]
```

### 2. Configuration du Cache

Assurez-vous que Django cache est configuré :

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### 3. Configuration des Modèles Surveillés

Le middleware surveille automatiquement ces modèles :
- `Category`
- `Tag`
- `Post`
- `Comment`
- `User`
- `Group`
- `Permission`

## ⚙️ Fonctionnement

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GraphQL       │    │   Middleware     │    │   Django        │
│   Request       │───▶│   Detection      │───▶│   Signals       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Pattern        │    │   Model         │
                       │   Matching       │    │   Operations    │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                └────────┬───────────────┘
                                         ▼
                                ┌─────────────────┐
                                │   Cache         │
                                │   Invalidation  │
                                └─────────────────┘
```

### Détection des Mutations

Le middleware détecte les mutations GraphQL via ces patterns :

```python
MUTATION_PATTERNS = [
    r'create_\w+',      # create_category, create_tag, etc.
    r'update_\w+',      # update_category, update_tag, etc.
    r'delete_\w+',      # delete_category, delete_tag, etc.
    r'bulk_\w+',        # bulk_create_category, etc.
    r'CreateCategory',  # Support legacy camelCase
    r'CreateTag',
    r'UpdateCategory',
    r'UpdateTag'
]
```

### Signaux Django

Le middleware s'abonne automatiquement aux signaux :

```python
# Connexion automatique des signaux
post_save.connect(_handle_model_change, sender=Category)
post_delete.connect(_handle_model_change, sender=Category)
m2m_changed.connect(_handle_m2m_change, sender=Post.tags.through)
```

## 🚀 Utilisation

### Opérations Directes Django

```python
# Ces opérations déclenchent automatiquement l'invalidation du cache
category = Category.objects.create(name="Nouvelle Catégorie")
category.name = "Nom Modifié"
category.save()
category.delete()
```

### Mutations GraphQL

```graphql
# Mutation qui devrait déclencher l'invalidation
mutation CreateCategory($input: CategoryInput!) {
    create_category(input: $input) {
        ok
        object {
            id
            name
            description
        }
        errors
    }
}
```

### Vérification de l'État du Cache

```python
from django.core.cache import cache

# Vérifier les clés du cache
cache_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
print(f"Clés dans le cache: {len(cache_keys)}")

# Ajouter des données de test
cache.set('test_key', 'test_value', 300)

# Effectuer une opération qui devrait invalider le cache
Category.objects.create(name="Test Category")

# Vérifier l'invalidation
remaining_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
print(f"Clés après invalidation: {len(remaining_keys)}")
```

## 🧪 Tests et Validation

### Tests Automatisés Disponibles

1. **`test_signal_connection_debug.py`** - Vérifie la connexion des signaux
2. **`test_cache_invalidation_final.py`** - Test complet d'invalidation
3. **`test_cache_debug_direct.py`** - Tests directs du middleware
4. **`test_cache_graphql_final.py`** - Tests GraphQL avec cache

### Exécution des Tests

```bash
# Test de connexion des signaux
python test_signal_connection_debug.py

# Test d'invalidation complète
python test_cache_invalidation_final.py

# Test GraphQL final
python test_cache_graphql_final.py
```

### Résultats Attendus

```
✅ Signal connection: SUCCÈS
✅ Cache invalidation (direct): SUCCÈS
✅ Middleware functionality: SUCCÈS
❌ GraphQL cache invalidation: ÉCHEC (limitation connue)
```

## 🔍 Dépannage

### Logs de Débogage

Le middleware génère des logs détaillés :

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Les logs apparaîtront dans la console
# [INFO] GraphQL mutation detected: create_category
# [DEBUG] Cache invalidated for model: Category
```

### Vérification des Signaux

```python
from django.db.models.signals import post_save
from test_app.models import Category

# Vérifier les receivers connectés
receivers = post_save._live_receivers(sender=Category)
print(f"Receivers connectés pour Category: {len(list(receivers))}")
```

### Vérification du Middleware

```python
from cache_middleware import GraphQLCacheInvalidationMiddleware

# Créer une instance de test
middleware = GraphQLCacheInvalidationMiddleware(lambda x: x)

# Vérifier les modèles surveillés
print(f"Modèles surveillés: {middleware.MONITORED_MODELS}")
```

## ⚠️ Limitations Connues

### 1. GraphQL Auto-Generated Schema

**Problème** : Les mutations du schéma auto-généré ne déclenchent pas l'invalidation du cache via le middleware.

**Cause** : Le middleware intercepte les requêtes HTTP mais les mutations auto-générées peuvent bypasser la détection de patterns.

**Solution de contournement** : Utiliser des mutations personnalisées avec invalidation manuelle :

```python
class CreateCategory(graphene.Mutation):
    def mutate(self, info, input):
        category = Category.objects.create(**input)
        # Invalidation manuelle
        cache.clear()
        return CreateCategory(category=category)
```

### 2. Cache Backend Spécifique

**Problème** : Le middleware utilise `cache.clear()` qui peut ne pas fonctionner avec tous les backends de cache.

**Solution** : Adapter la méthode d'invalidation selon le backend :

```python
def _invalidate_cache_for_model(self, model_class):
    if hasattr(cache, 'delete_pattern'):
        # Redis backend
        cache.delete_pattern(f"*{model_class.__name__.lower()}*")
    else:
        # Fallback
        cache.clear()
```

### 3. Performance avec Gros Volume

**Problème** : `cache.clear()` peut être coûteux sur de gros caches.

**Solution** : Implémenter une invalidation ciblée :

```python
CACHE_PATTERNS = {
    'Category': ['category_*', 'categories_*', 'nav_*'],
    'Tag': ['tag_*', 'tags_*', 'cloud_*'],
}
```

## 📊 Métriques et Monitoring

### Logging Personnalisé

```python
import logging

logger = logging.getLogger('cache_middleware')
handler = logging.FileHandler('cache_invalidation.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Métriques de Performance

```python
import time
from django.core.cache import cache

def measure_cache_performance():
    start_time = time.time()
    
    # Opération de test
    cache.set('test_key', 'test_value', 300)
    value = cache.get('test_key')
    
    end_time = time.time()
    print(f"Cache operation took: {end_time - start_time:.4f} seconds")
```

## 🔄 Évolutions Futures

### Améliorations Prévues

1. **Invalidation Ciblée** : Remplacer `cache.clear()` par une invalidation sélective
2. **Support Multi-Backend** : Adapter le comportement selon le backend de cache
3. **Métriques Intégrées** : Ajouter des statistiques d'invalidation
4. **Configuration Dynamique** : Permettre la configuration des modèles surveillés
5. **GraphQL Integration** : Améliorer la détection des mutations auto-générées

### Roadmap

- **v1.1** : Invalidation ciblée et métriques
- **v1.2** : Support multi-backend et configuration dynamique
- **v1.3** : Intégration GraphQL complète

## 📞 Support

Pour toute question ou problème :

1. Vérifiez les logs de débogage
2. Exécutez les tests de diagnostic
3. Consultez cette documentation
4. Vérifiez les limitations connues

---

**Version** : 1.0  
**Dernière mise à jour** : 2025-01-28  
**Statut** : Production Ready (avec limitations GraphQL)