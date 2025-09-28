#!/usr/bin/env python
"""
Middleware personnalisé pour l'invalidation automatique du cache GraphQL
Ce middleware utilise les signaux Django pour invalider le cache sur tous les changements de données
"""

import json
import re
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-local storage pour éviter les invalidations multiples
_thread_local = threading.local()

class GraphQLCacheInvalidationMiddleware(MiddlewareMixin):
    """
    Middleware qui invalide automatiquement le cache après les mutations GraphQL
    et utilise les signaux Django pour invalider le cache sur tous les changements de données
    
    Ce middleware:
    1. Détecte les requêtes GraphQL de type mutation
    2. Invalide le cache après l'exécution de la mutation
    3. Utilise les signaux Django pour capturer tous les changements de données
    4. Supporte les mutations auto-générées et personnalisées
    5. Invalide le cache pour toute modification CRUD en base de données
    """
    
    # Patterns de mutations à surveiller
    MUTATION_PATTERNS = [
        r'create_\w+',      # create_category, create_tag, etc.
        r'update_\w+',      # update_category, update_tag, etc.
        r'delete_\w+',      # delete_category, delete_tag, etc.
        r'CreateCategory',  # Mutations personnalisées
        r'CreateTag',
        r'UpdateTag',
        r'DeleteTag',
    ]
    
    # Configuration des modèles à surveiller
    MONITORED_APPS = getattr(settings, 'GRAPHQL_CACHE_MONITORED_APPS', ['test_app', 'tests'])
    EXCLUDED_MODELS = getattr(settings, 'GRAPHQL_CACHE_EXCLUDED_MODELS', ['Session', 'LogEntry', 'ContentType'])
    
    _signals_connected = False
    _lock = threading.Lock()
    
    def __init__(self, get_response):
        """
        Initialise le middleware et connecte les signaux Django
        
        Args:
            get_response: Fonction de réponse Django
        """
        self.get_response = get_response
        super().__init__(get_response)
        
        # Connecter les signaux une seule fois
        with self._lock:
            if not GraphQLCacheInvalidationMiddleware._signals_connected:
                self._connect_signals()
                GraphQLCacheInvalidationMiddleware._signals_connected = True
                logger.info("Signaux Django connectés pour l'invalidation du cache GraphQL")
    
    def _connect_signals(self):
        """
        Connecte les signaux Django pour surveiller tous les changements de données
        """
        # Connecter les signaux pour tous les modèles surveillés
        for app_label in self.MONITORED_APPS:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    model_name = model.__name__
                    
                    # Exclure certains modèles système
                    if model_name in self.EXCLUDED_MODELS:
                        continue
                    
                    # Connecter les signaux pour ce modèle avec des méthodes statiques
                    post_save.connect(
                        GraphQLCacheInvalidationMiddleware._handle_model_change,
                        sender=model,
                        dispatch_uid=f'cache_invalidation_save_{app_label}_{model_name}'
                    )
                    
                    post_delete.connect(
                        GraphQLCacheInvalidationMiddleware._handle_model_change,
                        sender=model,
                        dispatch_uid=f'cache_invalidation_delete_{app_label}_{model_name}'
                    )
                    
                    # Connecter les signaux many-to-many si le modèle en a
                    for field in model._meta.get_fields():
                        if field.many_to_many:
                            # Vérifier si le champ a un attribut 'through'
                            through_model = getattr(field, 'through', None)
                            if through_model is None and hasattr(field, 'remote_field'):
                                through_model = getattr(field.remote_field, 'through', None)
                            
                            if through_model:
                                m2m_changed.connect(
                                    GraphQLCacheInvalidationMiddleware._handle_m2m_change,
                                    sender=through_model,
                                    dispatch_uid=f'cache_invalidation_m2m_{app_label}_{model_name}_{field.name}'
                                )
                                logger.debug(f"Signal M2M connecté pour {app_label}.{model_name}.{field.name}")
                            else:
                                logger.debug(f"Pas de modèle through trouvé pour {app_label}.{model_name}.{field.name}")
                    
                    logger.info(f"Signaux connectés pour le modèle {app_label}.{model_name}")
                    
            except LookupError:
                logger.warning(f"Application '{app_label}' non trouvée pour la surveillance du cache")
    
    @staticmethod
    def _handle_model_change(sender, instance, **kwargs):
        """
        Gestionnaire de signal pour les changements de modèle (save/delete)
        
        Args:
            sender: Classe du modèle
            instance: Instance modifiée
            **kwargs: Arguments supplémentaires du signal
        """
        # Éviter les invalidations multiples dans le même thread
        if not hasattr(_thread_local, 'invalidation_pending'):
            _thread_local.invalidation_pending = set()
        
        model_key = f"{sender._meta.app_label}.{sender._meta.model_name}"
        
        if model_key not in _thread_local.invalidation_pending:
            _thread_local.invalidation_pending.add(model_key)
            
            # Invalider le cache
            GraphQLCacheInvalidationMiddleware._invalidate_cache_for_model(sender, instance)
            
            logger.info(f"Cache invalidé pour {model_key} (ID: {getattr(instance, 'pk', 'N/A')})")
    
    @staticmethod
    def _handle_m2m_change(sender, instance, action, pk_set, **kwargs):
        """
        Gestionnaire de signal pour les changements many-to-many
        
        Args:
            sender: Classe intermédiaire
            instance: Instance principale
            action: Type d'action (pre_add, post_add, pre_remove, post_remove, pre_clear, post_clear)
            pk_set: Set des clés primaires affectées
            **kwargs: Arguments supplémentaires
        """
        # Invalider seulement sur les actions post (après modification)
        if action in ['post_add', 'post_remove', 'post_clear']:
            model_key = f"{instance._meta.app_label}.{instance._meta.model_name}"
            
            GraphQLCacheInvalidationMiddleware._invalidate_cache_for_model(
                instance.__class__, 
                instance
            )
            
            logger.info(f"Cache invalidé pour relation M2M {model_key} (action: {action})")
    
    @staticmethod
    def _invalidate_cache_for_model(model_class, instance=None):
        """
        Invalide le cache pour un modèle spécifique
        
        Args:
            model_class: Classe du modèle
            instance: Instance spécifique (optionnel)
        """
        try:
            # Stratégie 1: Effacement complet du cache (plus sûr)
            cache.clear()
            
            # Stratégie 2: Invalidation ciblée (si implémentée)
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name.lower()
            
            # Patterns de clés à invalider
            cache_patterns = [
                f"graphql:*",
                f"query:*",
                f"schema:*",
                f"{model_name}:*",
                f"{app_label}_{model_name}:*",
                f"field:{model_name}:*",
            ]
            
            # Si on a une instance spécifique, invalider aussi ses clés
            if instance and hasattr(instance, 'pk'):
                cache_patterns.extend([
                    f"{model_name}:{instance.pk}:*",
                    f"{app_label}_{model_name}:{instance.pk}:*",
                ])
            
            # Tentative d'invalidation par pattern (dépend du backend de cache)
            for pattern in cache_patterns:
                try:
                    # Cette méthode dépend du backend de cache
                    # Pour Redis: cache.delete_pattern(pattern)
                    # Pour maintenant, on utilise l'effacement complet ci-dessus
                    pass
                except AttributeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache pour {model_class}: {e}")
    
    def process_request(self, request):
        """
        Traite la requête entrante et initialise le contexte d'invalidation
        
        Args:
            request: Requête HTTP Django
            
        Returns:
            None ou HttpResponse
        """
        # Réinitialiser le contexte d'invalidation pour cette requête
        _thread_local.invalidation_pending = set()
        
        # Marquer si c'est une mutation GraphQL
        request._is_graphql_mutation = False
        
        if request.path == '/graphql/' and request.method == 'POST':
            try:
                if hasattr(request, 'body') and request.body:
                    body = json.loads(request.body.decode('utf-8'))
                    query = body.get('query', '')
                    
                    # Vérifier si c'est une mutation
                    if self._is_mutation_query(query):
                        request._is_graphql_mutation = True
                        logger.info(f"Mutation GraphQL détectée: {self._extract_mutation_name(query)}")
                        
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Erreur lors du parsing de la requête GraphQL: {e}")
                
        return None
    
    def process_response(self, request, response):
        """
        Traite la réponse après exécution et nettoie le contexte
        
        Args:
            request: Requête HTTP Django
            response: Réponse HTTP Django
            
        Returns:
            HttpResponse: Réponse modifiée
        """
        # Si c'était une mutation GraphQL, vérifier si elle a réussi
        if getattr(request, '_is_graphql_mutation', False):
            try:
                # Vérifier si la mutation a réussi
                if self._mutation_successful(response):
                    # L'invalidation a déjà été faite par les signaux
                    # mais on peut ajouter une invalidation supplémentaire si nécessaire
                    logger.info("Mutation GraphQL réussie - cache déjà invalidé par les signaux")
                else:
                    logger.info("Mutation GraphQL échouée, pas d'invalidation supplémentaire")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de la mutation: {e}")
        
        # Nettoyer le contexte d'invalidation
        if hasattr(_thread_local, 'invalidation_pending'):
            delattr(_thread_local, 'invalidation_pending')
                
        return response
    
    def _is_mutation_query(self, query):
        """
        Vérifie si la requête est une mutation
        
        Args:
            query (str): Requête GraphQL
            
        Returns:
            bool: True si c'est une mutation
        """
        if not query:
            return False
            
        # Vérifier le mot-clé mutation
        if re.search(r'\bmutation\b', query, re.IGNORECASE):
            return True
            
        # Vérifier les patterns de mutations spécifiques
        for pattern in self.MUTATION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        return False
    
    def _extract_mutation_name(self, query):
        """
        Extrait le nom de la mutation de la requête
        
        Args:
            query (str): Requête GraphQL
            
        Returns:
            str: Nom de la mutation ou 'unknown'
        """
        try:
            # Chercher le nom de la mutation après le mot-clé mutation
            match = re.search(r'mutation\s+(\w+)', query, re.IGNORECASE)
            if match:
                return match.group(1)
                
            # Chercher les patterns de mutations dans le corps
            for pattern in self.MUTATION_PATTERNS:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    return match.group(0)
                    
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction du nom de mutation: {e}")
            
        return 'unknown'
    
    def _mutation_successful(self, response):
        """
        Vérifie si la mutation a réussi
        
        Args:
            response: Réponse HTTP Django
            
        Returns:
            bool: True si la mutation a réussi
        """
        try:
            # Vérifier le code de statut HTTP
            if response.status_code != 200:
                return False
                
            # Si c'est une JsonResponse, vérifier le contenu
            if isinstance(response, JsonResponse):
                content = json.loads(response.content.decode('utf-8'))
            else:
                content = json.loads(response.content.decode('utf-8'))
                
            # Vérifier s'il y a des erreurs GraphQL
            if 'errors' in content and content['errors']:
                return False
                
            # Vérifier si les données sont présentes
            if 'data' in content and content['data']:
                # Pour les mutations auto-générées, vérifier le champ 'ok'
                data = content['data']
                for key, value in data.items():
                    if isinstance(value, dict) and 'ok' in value:
                        return value['ok'] is True
                        
                # Si pas de champ 'ok', considérer comme réussi si pas d'erreurs
                return True
                
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.warning(f"Erreur lors de la vérification du succès de la mutation: {e}")
            
        return False
    

    



class GraphQLCacheConfig:
    """
    Configuration pour le cache GraphQL avec invalidation automatique
    """
    
    @staticmethod
    def get_middleware_config():
        """
        Retourne la configuration du middleware pour Django settings
        
        Returns:
            str: Chemin du middleware à ajouter dans MIDDLEWARE
        """
        return 'cache_middleware.GraphQLCacheInvalidationMiddleware'
    
    @staticmethod
    def get_cache_settings():
        """
        Retourne les paramètres de cache recommandés
        
        Returns:
            dict: Configuration de cache pour Django settings
        """
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'graphql-cache',
                'TIMEOUT': 300,  # 5 minutes
                'OPTIONS': {
                    'MAX_ENTRIES': 1000,
                    'CULL_FREQUENCY': 3,
                }
            }
        }
    
    @staticmethod
    def get_logging_config():
        """
        Retourne la configuration de logging pour le middleware
        
        Returns:
            dict: Configuration de logging
        """
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'cache_file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'graphql_cache.log',
                    'formatter': 'verbose',
                },
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
            },
            'loggers': {
                'cache_middleware': {
                    'handlers': ['cache_file', 'console'],
                    'level': 'INFO',
                    'propagate': True,
                },
            },
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
                'simple': {
                    'format': '{levelname} {message}',
                    'style': '{',
                },
            },
        }


# Fonction utilitaire pour l'installation
def install_cache_middleware():
    """
    Instructions pour installer le middleware dans Django
    
    Cette fonction affiche les instructions pour configurer le middleware
    """
    print("🔧 INSTALLATION DU MIDDLEWARE DE CACHE")
    print("=" * 50)
    print("\n1. Ajouter le middleware dans settings.py:")
    print("   MIDDLEWARE = [")
    print("       # ... autres middlewares ...")
    print("       'cache_middleware.GraphQLCacheInvalidationMiddleware',")
    print("   ]")
    
    print("\n2. Configuration du cache (optionnel):")
    print("   CACHES = {")
    print("       'default': {")
    print("           'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',")
    print("           'LOCATION': 'graphql-cache',")
    print("           'TIMEOUT': 300,")
    print("       }")
    print("   }")
    
    print("\n3. Configuration du logging (optionnel):")
    print("   LOGGING = {")
    print("       'loggers': {")
    print("           'cache_middleware': {")
    print("               'level': 'INFO',")
    print("               'handlers': ['console'],")
    print("           }")
    print("       }")
    print("   }")
    
    print("\n✅ Le middleware invalidera automatiquement le cache après chaque mutation!")

if __name__ == "__main__":
    install_cache_middleware()