"""
Configuration de l'application Django GraphQL Auto.

Ce module configure:
- Application Django pour la génération automatique de schémas GraphQL
- Configuration des signaux et hooks
- Initialisation des composants principaux
"""
from rail_django_graphql.middleware.performance import setup_performance_monitoring
setup_performance_monitoring()
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class DjangoGraphQLAutoConfig(AppConfig):
    """Configuration de l'application Django GraphQL Auto."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rail_django_graphql'
    verbose_name = 'Django GraphQL Auto Generation'
    
    def ready(self):
        """Initialisation de l'application après le chargement de Django."""
        try:
            # Importer les signaux si nécessaire
            self._setup_signals()
            
            # Configuration de l'environnement
            self._configure_environment()
            
            logger.info("Django GraphQL Auto application initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Django GraphQL Auto: {e}")
    
    def _setup_signals(self):
        """Configure les signaux Django pour la génération automatique."""
        try:
            # Éviter les imports circulaires en important ici
            from .core.schema import SchemaBuilder
            
            # Les signaux seront configurés par le SchemaBuilder
            # quand il sera instancié
            pass
            
        except ImportError as e:
            logger.warning(f"Could not setup signals: {e}")
    
    def _configure_environment(self):
        """Configure l'environnement pour l'application."""
        import os
        
        # Configuration des logs pour l'application
        logging.getLogger('rail_django_graphql').setLevel(
            logging.DEBUG if os.environ.get('DEBUG') else logging.INFO
        )